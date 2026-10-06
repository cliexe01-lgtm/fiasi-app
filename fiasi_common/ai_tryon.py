"""Essayage virtuel IA FIASI.

Le client envoie :
- la photo de la cliente ;
- l'URL publique du modèle choisi dans le catalogue.

Deux modes sont supportés :
1) AI_BACKEND_URL : recommandé en production. Un serveur sécurisé garde la clé OpenAI.
2) OPENAI_API_KEY : mode direct de test. Ne pas embarquer une vraie clé dans une APK publique.

L'API Images d'OpenAI accepte plusieurs images de référence pour un edit.
"""
from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request

from . import config


class AIError(Exception):
    pass


def _read_client_image(value: str) -> str:
    """Transforme un chemin local en data URL; une data URL est conservée telle quelle."""
    if value.startswith("data:image/"):
        return value
    if not os.path.isfile(value):
        raise AIError("La photo de la cliente est introuvable.")
    data = open(value, "rb").read()
    mime = mimetypes.guess_type(value)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def _read_reference_image(value: str) -> str:
    """Télécharge la miniature du catalogue et la convertit en data URL."""
    if value.startswith("data:image/"):
        return value
    if os.path.isfile(value):
        try:
            data = open(value, "rb").read()
            if len(data) > 20 * 1024 * 1024:
                raise AIError("L'image du catalogue est trop volumineuse.")
            mime = mimetypes.guess_type(value)[0] or "image/jpeg"
            if not mime.startswith("image/"):
                raise AIError("La référence du catalogue n'est pas une image.")
            return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
        except AIError:
            raise
        except Exception as exc:
            raise AIError(f"Impossible de lire la photo du modèle : {exc}") from exc

    if value.startswith("data:image/"):
        return value
    if not value.startswith(("http://", "https://")):
        raise AIError("La référence de coiffure n'est pas valide.")
    try:
        request = urllib.request.Request(value, headers={"User-Agent": "FIASI/1.0 image-catalog"})
        with urllib.request.urlopen(request, timeout=35) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
        if not content_type.startswith("image/"):
            raise AIError("La référence du catalogue n'est pas une image.")
        if len(data) > 20 * 1024 * 1024:
            raise AIError("L'image du catalogue est trop volumineuse.")
        return f"data:{content_type};base64," + base64.b64encode(data).decode("ascii")
    except AIError:
        raise
    except Exception as exc:
        raise AIError(f"Impossible de récupérer la photo du modèle : {exc}") from exc


def _post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, method="POST", headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise AIError(f"Serveur IA HTTP {exc.code}: {detail[:1200]}") from exc
    except Exception as exc:
        raise AIError(f"Connexion au service IA impossible : {exc}") from exc
    try:
        result = json.loads(raw)
    except Exception as exc:
        raise AIError("Le service IA a renvoyé une réponse invalide.") from exc
    if isinstance(result, dict) and result.get("error"):
        raise AIError(str(result["error"]))
    return result


def _extract_image(result: dict) -> str:
    try:
        item = result["data"][0]
        b64 = item.get("b64_json")
        if b64:
            base64.b64decode(b64, validate=True)
            return "data:image/png;base64," + b64
        url = item.get("url")
        if url:
            return url
    except Exception:
        pass
    raise AIError("Le service IA n'a fourni aucune image. Réponse reçue : " + str(result)[:800])


async def generate_tryon(
    client_photo: str,
    hairstyle_reference: str,
    prompt: str | None = None,
    style_name: str = "",
) -> str:
    """Génère le rendu IA à partir de la photo cliente et du modèle choisi."""
    client_image = _read_client_image(client_photo)

    hairstyle_image = await asyncio.to_thread(_read_reference_image, hairstyle_reference)

    instruction = prompt or f"""
Create a photorealistic beauty try-on for a salon application.

REFERENCE IMAGE 1 = the real client. This is the identity reference.
REFERENCE IMAGE 2 = the selected hairstyle/wig reference.

Apply the hairstyle from reference image 2 to the client in reference image 1.
Preserve the client's identity, face, skin tone, facial structure, age and natural
features. Do not copy the face of the model in reference image 2. Only change the
hair/head styling required to reproduce the selected hairstyle or wig.

Keep realistic hairline integration, proportions, lighting, shadows and texture.
Keep the client's clothing and background as unchanged as practical.
Do not beautify or reshape the face.
The result must look like a realistic salon preview, not an illustration.

Selected style: {style_name or "selected hairstyle"}.
""".strip()

    payload = {
        "model": config.OPENAI_IMAGE_MODEL,
        "images": [
            {"image_url": client_image},
            {"image_url": hairstyle_image},
        ],
        "prompt": instruction,
        "size": "1024x1536",
        "quality": "medium",
        "n": 1,
    }

    # Mode recommandé : clé gardée côté serveur.
    if config.AI_BACKEND_URL.strip():
        result = await asyncio.to_thread(
            _post_json,
            config.AI_BACKEND_URL.strip(),
            {
                "client_image": client_image,
                "style_image": hairstyle_image,
                "prompt": instruction,
                "model": config.OPENAI_IMAGE_MODEL,
            },
        )
        return _extract_image(result)

    # Mode direct réservé aux tests locaux.
    api_key = config.OPENAI_API_KEY.strip()
    if not api_key or api_key.startswith("COLLE_"):
        raise AIError(
            "Le service IA n'est pas configuré. Déployez le backend FIASI fourni "
            "dans firebase/functions puis renseignez AI_BACKEND_URL, ou utilisez "
            "OPENAI_API_KEY uniquement pour un test local."
        )

    result = await asyncio.to_thread(
        _post_json,
        "https://api.openai.com/v1/images/edits",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )
    return _extract_image(result)
