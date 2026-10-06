"""
config.py — Réglages communs aux deux applications.

Vous pouvez soit :
  1) modifier directement les valeurs ci-dessous (le plus simple, et le SEUL moyen en
     version web/Pyodide où les variables d'environnement n'existent pas),
  2) soit définir les variables d'environnement FIASI_FIREBASE_DB_URL / FIASI_FIREBASE_AUTH
     (pratique en développement sur ordinateur).
"""
import os

# ---------------------------------------------------------------------------
# FIREBASE
# ---------------------------------------------------------------------------
# URL de votre Realtime Database (Console Firebase > Build > Realtime Database).
# Exemple : "https://fiasi-beauty-default-rtdb.europe-west1.firebasedatabase.app"
#
# Si cette valeur est VIDE, les apps tournent en "MODE DÉMO LOCAL" :
#   - sur ordinateur : les deux apps partagent un fichier JSON temporaire,
#     donc elles communiquent entre elles sur la même machine (pratique pour tester) ;
#   - sur le web (Pyodide) : les données restent en mémoire, sans partage.
FIREBASE_DB_URL = os.environ.get("FIASI_FIREBASE_DB_URL", "https://fiasi-app-default-rtdb.firebaseio.com")

# Jeton optionnel ajouté en `?auth=...` à chaque requête REST.
# Utile si vos règles Firebase exigent une authentification
# (idToken Firebase Auth, ou "database secret" en développement uniquement).
FIREBASE_AUTH = os.environ.get("FIASI_FIREBASE_AUTH", "")

# ---------------------------------------------------------------------------
# SYNCHRONISATION
# ---------------------------------------------------------------------------
# Les deux apps interrogent Firebase toutes les N secondes ("polling").
# C'est volontairement simple : le streaming temps réel de Firebase passe par
# EventSource/SSE, difficile à utiliser sous Pyodide. 5 s est un bon compromis.
POLL_SECONDS = 5

# Si True, l'app Réception crée quelques réservations de démonstration quand la
# base est vide. Mettez False en production.
SEED_DEMO_DATA = False

# Fichier JSON utilisé par le mode démo local (desktop). Vide = fichier temporaire.
LOCAL_DB_FILE = os.environ.get("FIASI_LOCAL_DB", "")

# ---------------------------------------------------------------------------
# IA ESSAYAGE COIFFURE (CLIENT)
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "COLLE_TA_CLE_OPENAI_ICI")
OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")

# URL du backend sécurisé FIASI qui garde la clé OpenAI côté serveur.
# Exemple : https://<region>-<project>.cloudfunctions.net/fiasiTryon
AI_BACKEND_URL = os.environ.get("FIASI_AI_BACKEND_URL", "https://europe-west1-fiasi-app.cloudfunctions.net/fiasiTryon")
