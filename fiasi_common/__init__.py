"""
fiasi_common — Code PARTAGÉ entre l'app Cliente et l'app Réception FIASI.

Contenu :
    config.py          -> réglages (URL Firebase, fréquence de synchro…)
    models.py          -> données métier (statuts, prestations, Booking…)
    firebase_client.py -> accès Firebase Realtime Database via REST (compatible Pyodide)
    repository.py      -> fonctions "métier" (créer / lister / modifier une réservation)
    ui.py              -> petits composants Flet réutilisables (boutons, toast, modale…)

⚠️  Ce dossier `common/` est la SOURCE DE VÉRITÉ. Après chaque modification, lancez :
        python tools/sync_common.py
    pour le recopier dans client_app/src/ et reception_app/src/
    (chaque app doit embarquer sa propre copie pour que `flet build` fonctionne).
"""
