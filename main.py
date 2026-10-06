"""
main.py — Point d'entrée de l'application CLIENTE FIASI (Flet 0.80.2).

Lancer sur ordinateur :      flet run src/main.py        (ou  python src/main.py)
Lancer dans le navigateur :  flet run --web src/main.py
Construire :                 flet build web   |   flet build apk   |   flet build ipa
"""
import flet as ft

from app import FiasiClient


def main(page: ft.Page):
    # Toute la logique est dans FiasiClient (voir app.py) ; main() ne fait que le démarrer.
    FiasiClient(page).start()


if __name__ == "__main__":
    # assets_dir : dossier contenant logo.png (chemin relatif à ce fichier).
    # Flet 0.80 : ft.run() remplace ft.app() (qui reste accepté mais est déprécié).
    runner = getattr(ft, "run", None) or ft.app
    runner(main, assets_dir="assets")
