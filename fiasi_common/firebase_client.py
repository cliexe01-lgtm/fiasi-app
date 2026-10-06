"""
firebase_client.py — Accès à Firebase Realtime Database via son API REST.

POURQUOI REST ET PAS firebase_admin / pyrebase ?
    Flet 0.80.2 en version web tourne sous Pyodide 0.27.7 (Python dans le navigateur).
    Les SDK Firebase Python reposent sur grpc / des sockets : ils ne s'installent pas
    sous Pyodide. L'API REST de Realtime Database, elle, n'est que du HTTP + JSON,
    donc elle fonctionne PARTOUT (web, Android, iOS, desktop) avec le même code.

DEUX "STORES" AVEC LA MÊME INTERFACE (get / put / patch / post / delete) :
    - RemoteStore : parle à Firebase (si FIREBASE_DB_URL est renseignée)
    - LocalStore  : simule Firebase en local (mode démo) — voir config.py

TRANSPORT HTTP :
    - Pyodide (navigateur)  -> `pyodide.http.pyfetch` (équivalent de fetch() JavaScript)
    - Autres plateformes    -> `urllib` dans un thread (pour ne pas bloquer l'interface)
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import random
import string
import sys
import tempfile
import time
from urllib.parse import quote

from . import config

# True quand le code tourne dans le navigateur (Flet web = Pyodide = WebAssembly).
IS_PYODIDE = sys.platform == "emscripten"


class FirebaseError(Exception):
    """Erreur réseau ou réponse HTTP >= 400 de Firebase."""


# ===========================================================================
# 1) TRANSPORT HTTP
# ===========================================================================
async def _http(method: str, url: str, body=None, timeout: int = 15):
    """Envoie une requête HTTP et renvoie (code_http, texte_réponse)."""
    payload = None if body is None else json.dumps(body, ensure_ascii=False)

    # --- Cas navigateur (Pyodide) -------------------------------------------------
    if IS_PYODIDE:
        from pyodide.http import pyfetch  # n'existe que sous Pyodide

        kwargs = {"method": method, "headers": {"Content-Type": "application/json"}}
        if payload is not None:
            kwargs["body"] = payload
        resp = await pyfetch(url, **kwargs)
        return resp.status, await resp.string()

    # --- Cas Android / iOS / desktop ----------------------------------------------
    import urllib.error
    import urllib.request

    # Sur Android, le magasin de certificats système n'est pas toujours visible de
    # Python : si le paquet `certifi` est installé, on l'utilise pour valider le HTTPS.
    ssl_ctx = None
    try:
        import ssl
        import certifi
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    def _blocking():
        req = urllib.request.Request(
            url,
            data=payload.encode("utf-8") if payload is not None else None,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:      # 4xx / 5xx : on renvoie le code
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:                    # pas de réseau, DNS, timeout…
            raise FirebaseError(f"Réseau indisponible : {e}") from e

    # asyncio.to_thread : l'appel bloquant s'exécute hors du thread de l'interface.
    return await asyncio.to_thread(_blocking)


# ===========================================================================
# 2) STORE DISTANT : Firebase Realtime Database (REST)
# ===========================================================================
class RemoteStore:
    """Chaque 'chemin' (ex: 'bookings/F-1028') correspond à l'URL  <base>/<chemin>.json"""

    is_remote = True
    label = "Firebase"

    def __init__(self, base_url: str, auth: str = ""):
        self.base = base_url.rstrip("/")
        self.auth = auth

    def _url(self, path: str, params: dict | None = None) -> str:
        q = dict(params or {})
        if self.auth:
            q["auth"] = self.auth
        qs = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in q.items())
        return f"{self.base}/{path.strip('/')}.json" + (f"?{qs}" if qs else "")

    async def _call(self, method, path, body=None, params=None):
        status, text = await _http(method, self._url(path, params), body)
        if status >= 400:
            raise FirebaseError(f"HTTP {status} sur {method} /{path} : {text[:200]}")
        return json.loads(text) if text else None

    # --- Lecture -------------------------------------------------------------------
    async def get(self, path, order_by=None, equal_to=None, limit_last=None):
        """
        Lit un nœud. Options (requêtes Firebase) :
          order_by="$key" + limit_last=20   -> les 20 dernières entrées (clés push = chronologiques)
          order_by="phone_key" + equal_to="228..." -> filtre sur un champ
        ⚠️ Filtrer sur un champ exige `.indexOn` dans les règles (voir dossier firebase/).
        """
        params = {}
        if order_by:
            params["orderBy"] = json.dumps(order_by)       # Firebase veut "\"champ\""
        if equal_to is not None:
            params["equalTo"] = json.dumps(equal_to)
        if limit_last:
            params["limitToLast"] = int(limit_last)
        return await self._call("GET", path, params=params)

    # --- Écriture ------------------------------------------------------------------
    async def put(self, path, value):      # remplace tout le nœud
        return await self._call("PUT", path, value)

    async def patch(self, path, changes):  # modifie seulement certains champs
        return await self._call("PATCH", path, changes)

    async def post(self, path, value):     # ajoute avec une clé auto ("push")
        res = await self._call("POST", path, value)
        return (res or {}).get("name")

    async def delete(self, path):
        return await self._call("DELETE", path)


# ===========================================================================
# 3) STORE LOCAL : imite Firebase pour tester sans compte
# ===========================================================================
def _parts(path: str):
    return [p for p in path.strip("/").split("/") if p]


def _push_key() -> str:
    """Clé triable par date, comme les clés 'push' de Firebase."""
    rnd = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    return f"{int(time.time() * 1000):013d}{rnd}"


class LocalStore:
    """
    Données dans un dict Python.
    - Sur ordinateur : persisté dans un fichier JSON PARTAGÉ → l'app Cliente et l'app
      Réception lancées sur la même machine communiquent vraiment entre elles.
    - Sous Pyodide : mémoire seule (pas de fichier partagé possible).
    """

    is_remote = False
    label = "Démo locale"

    def __init__(self, file_path: str | None = None):
        self.file = file_path
        self.data: dict = {}

    # -- persistance ------------------------------------------------------------
    def _load(self):
        if self.file and os.path.exists(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    self.data = json.load(f) or {}
            except Exception:
                pass  # fichier en cours d'écriture par l'autre app : on garde l'état

    def _save(self):
        if self.file:
            tmp = self.file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False)
            os.replace(tmp, self.file)  # remplacement atomique

    # -- navigation dans l'arbre --------------------------------------------------
    def _read(self, path):
        node = self.data
        for p in _parts(path):
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return copy.deepcopy(node)

    def _write(self, path, value):
        parts = _parts(path)
        if not parts:
            self.data = value or {}
            return
        node = self.data
        for p in parts[:-1]:
            if not isinstance(node.get(p), dict):
                node[p] = {}
            node = node[p]
        if value is None:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value

    # -- même interface que RemoteStore -------------------------------------------
    async def get(self, path, order_by=None, equal_to=None, limit_last=None):
        self._load()
        node = self._read(path)
        if isinstance(node, dict) and order_by:
            if order_by == "$key":
                items = sorted(node.items(), key=lambda kv: kv[0])
            else:
                items = [(k, v) for k, v in node.items()
                         if isinstance(v, dict) and (equal_to is None or v.get(order_by) == equal_to)]
            if limit_last:
                items = items[-int(limit_last):]
            node = dict(items)
        return node

    async def put(self, path, value):
        self._load(); self._write(path, copy.deepcopy(value)); self._save()
        return value

    async def patch(self, path, changes):
        self._load()
        cur = self._read(path)
        cur = cur if isinstance(cur, dict) else {}
        cur.update(copy.deepcopy(changes))
        self._write(path, cur); self._save()
        return changes

    async def post(self, path, value):
        key = _push_key()
        await self.put(f"{path.strip('/')}/{key}", value)
        return key

    async def delete(self, path):
        self._load(); self._write(path, None); self._save()


# ===========================================================================
# 4) FABRIQUE
# ===========================================================================
def make_store():
    """Renvoie RemoteStore si une URL Firebase est configurée, sinon LocalStore."""
    if config.FIREBASE_DB_URL.strip():
        return RemoteStore(config.FIREBASE_DB_URL.strip(), config.FIREBASE_AUTH.strip())
    path = None
    if not IS_PYODIDE:
        path = config.LOCAL_DB_FILE or os.path.join(tempfile.gettempdir(), "fiasi_local_db.json")
    return LocalStore(path)
