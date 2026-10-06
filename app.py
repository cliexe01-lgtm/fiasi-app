"""
app.py — Contrôleur de l'application CLIENTE FIASI.

Il remplace la partie <script> du HTML :
    showPage / backPage          -> show_page / back_page
    openService / bookServiceDirect / startBooking -> open_category / book_service_direct / start_booking_from_detail
    checkAvailability            -> check_availability
    confirmBooking               -> confirm_booking   (ÉCRIT dans Firebase !)
    photoModal                   -> open_photo_modal
    toast()                      -> self.toast.show()

CE QUI EST NOUVEAU PAR RAPPORT AU HTML (interaction via Firebase) :
    1. confirm_booking() enregistre la réservation dans /bookings/{id}.
    2. Une tâche de fond (poll_loop) relit les réservations de la cliente toutes les
       POLL_SECONDS secondes ; si la réception change un statut, la cliente reçoit
       une notification (toast) et la page « Mes réservations » se met à jour.
"""
from __future__ import annotations

import asyncio
import os
from datetime import date

import flet as ft

from fiasi_common import config
from fiasi_common.firebase_client import make_store
from fiasi_common.models import (
    CLIENT_STATUS_LABELS, HOME_CATEGORIES, SERVICES, TIME_SLOTS, Booking, digits,
    format_date_long, new_booking_id,
)
from fiasi_common.repository import Repository
from fiasi_common.ui import (
    BLACK, GOLD, INK, LINE, MUTED, SERIF, WHITE, Modal, T, Toast, btn, configure_window,
    pad_all,
)
from pages import PAGES, apply_hair, history_card, kicker, logo, service_line  # noqa: F401

PHONE_FRAME_WIDTH = 430   # largeur du "téléphone" quand l'app s'ouvre sur un grand écran


class FiasiClient:
    def __init__(self, page: ft.Page):
        self.page = page
        self.repo = Repository(make_store())     # accès Firebase en ligne

        # --- état de navigation (variables JS : current / previous) ----------------
        self.current = "home"
        self.previous = "home"
        self.catalog_expanded = False
        self.catalog_expanded_categories = set()
        self.image_catalog_expanded = False
        self.booking_service_expanded = False
        self.booking_category = None

        # --- état du formulaire de réservation (remplace les <input id="book...">) --
        self.form = {
            "name": "",                            # le client saisit son nom au moment de la réservation
            "service": "",                          # aucune prestation pré-sélectionnée
            "allowed": None,                       # liste de la catégorie si elle est connue
            "date": "",                            # la cliente choisit sa date
            "time": "",                            # la cliente choisit son heure
            "address": "",
            "phone": "",
            "notes": "",
            "extra": "",
        }

        # --- états divers ------------------------------------------------------------
        self.detail_service = SERVICES[0][0]     # prestation affichée sur la fiche détail
        self.cat_filter = "all"                  # chip actif du catalogue
        self.hair = ""                           # style de coiffure du simulateur
        self.client_photo_path = ""
        self.hairstyle_photo_path = ""
        self.client_photo_data_url = ""
        self.selected_tryon_style_url = ""
        self.selected_tryon_style_name = ""
        self.image_catalog_category = ""
        self.ai_result_src = ""
        self.ai_status = ""
        self.my_phone = ""                       # numéro servant à retrouver ses réservations
        self.my_bookings: list = []              # dernières réservations lues dans Firebase
        self._status_seen: dict = {}             # id -> dernier statut connu (détecte les changements)

        # références vers des contrôles recréés à chaque affichage de page
        self.history_list = None
        self.catalog_list = None
        self.hair_box = None
        self.wb = None                           # bloc animé « Comment ça marche ? »
        self.nav_buttons: dict = {}

    def _start_async(self, fn, *args):
        """Lance une coroutine FIASI sans dépendre directement de page.run_task."""
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(fn(*args))
        except RuntimeError:
            runner = getattr(self.page, "run_task", None)
            if callable(runner):
                return runner(fn, *args)
            raise RuntimeError("Cette version de Flet ne permet pas de lancer une tâche asynchrone.")

    # ======================================================================
    # DÉMARRAGE
    # ======================================================================
    def start(self):
        page = self.page
        configure_window(page, 430, 860, "FIASI — Application mobile")
        page.padding = 0
        page.spacing = 0
        page.bgcolor = WHITE
        page.theme_mode = ft.ThemeMode.LIGHT

        # Zone centrale où s'affiche la page courante
        self.screen = ft.Container(expand=True, bgcolor=WHITE)
        self.nav = self._build_nav()

        # Calques superposés (équivalents de .modal, .toast, .splash)
        self.modal = Modal(page, position="bottom")
        self.toast = Toast(page, bottom=92)
        self.splash = ft.Container(
            left=0, top=0, right=0, bottom=0, bgcolor=WHITE, alignment=ft.Alignment(0, 0), opacity=1,
            animate_opacity=600, content=logo(205),
        )

        # Cadre "téléphone" : on empile contenu + barre de navigation + calques
        self.frame = ft.Container(
            bgcolor=WHITE, expand=True,
            content=ft.Stack([
                ft.Container(content=self.screen, left=0, top=0, right=0, bottom=0),
                ft.Container(content=self.nav, left=0, right=0, bottom=0),
                self.modal.layer, self.toast.layer, self.splash,
            ], expand=True),
        )
        self.shell = ft.Row([self.frame], alignment=ft.MainAxisAlignment.CENTER, expand=True)
        page.add(self.shell)

        self.apply_layout()
        page.on_resize = lambda e: self.apply_layout()   # recalcul si la fenêtre change de taille

        self.show_page("home")
        self._start_async(self._hide_splash)
        self._start_async(self.poll_loop)

    def apply_layout(self):
        """Sur grand écran, on limite à 430 px (comme #app{max-width:430px} du CSS)."""
        w = self.page.width or 0
        if w and w > 600:
            self.frame.expand = False
            self.frame.width = PHONE_FRAME_WIDTH
        else:
            self.frame.width = None
            self.frame.expand = True
        self.page.update()

    async def _hide_splash(self):
        """Écran de démarrage : logo 1,6 s puis fondu (animation .splash du CSS)."""
        await asyncio.sleep(1.6)
        self.splash.opacity = 0
        self.page.update()
        await asyncio.sleep(0.7)
        self.splash.visible = False
        self.page.update()

    # ======================================================================
    # BARRE DE NAVIGATION DU BAS  (<nav class="bottom">)
    # ======================================================================
    def _build_nav(self):
        items = [("home", "⌂", "Accueil"), ("catalogue", "⌕", "Catalogue"),
                 ("booking", "＋", "Réserver"), ("history", "◷", "Mes RDV")]
        row = []
        for pid, icon, label in items:
            icon_t, label_t = T(icon, 20, "#888888"), T(label, 10, "#888888")
            self.nav_buttons[pid] = (icon_t, label_t)
            row.append(ft.Container(
                expand=True, on_click=lambda e, p=pid: self.show_page(p), ink=True,
                content=ft.Column([icon_t, label_t], spacing=4,
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  alignment=ft.MainAxisAlignment.CENTER)))
        return ft.Container(
            height=76, bgcolor=ft.Colors.with_opacity(0.97, WHITE),
            border=ft.Border(top=ft.BorderSide(1, LINE)), content=ft.Row(row, spacing=0))

    def _paint_nav(self):
        for pid, (icon_t, label_t) in self.nav_buttons.items():
            on = pid == self.current
            icon_t.color = GOLD if on else "#888888"
            label_t.color = INK if on else "#888888"

    # ======================================================================
    # NAVIGATION
    # ======================================================================
    def show_page(self, pid: str):
        """Affiche un écran (équivalent de showPage(id) en JS)."""
        self.previous, self.current = self.current, pid
        self.screen.content = PAGES[pid](self)      # on reconstruit l'écran à chaque affichage
        self._paint_nav()
        self.page.update()
        # L'ancien bloc animé utilisait une coroutine `run` qui provoquait
        # des erreurs selon la version Flet. Le catalogue est maintenant
        # statique et s'ouvre directement, sans tâche de fond.
        if pid == "history":
            self._start_async(self.refresh_bookings)

    def back_page(self):
        """Bouton retour ‹ (backPage() du JS)."""
        if self.current in ("detail", "try"):
            target = "catalogue"
        elif self.current == "booking":
            target = self.previous if self.previous not in ("booking", "detail", "try") else "home"
        else:
            target = "home"
        self.show_page(target)

    # ======================================================================
    # CATALOGUE
    # ======================================================================
    def fill_catalog(self):
        """Remplit la liste des prestations selon le chip actif."""
        self.catalog_list.controls = [
            service_line(self, name, cat_label) for name, cat, cat_label in SERVICES
            if self.cat_filter == "all" or cat == self.cat_filter
        ]

    def toggle_catalog_more(self):
        self.catalog_expanded = not getattr(self, "catalog_expanded", False)
        self.show_page("catalogue")

    def set_cat_filter(self, key):
        self.cat_filter = key
        self.catalog_expanded = False
        self.catalog_expanded_categories = set()
        self.fill_catalog()
        self.page.update()

    def open_detail(self, name):
        self.detail_service = name
        self.show_page("detail")

    # ======================================================================
    # DÉPART DE RÉSERVATION  (openService / bookServiceDirect / startBooking)
    # ======================================================================
    def open_category(self, category: str):
        names = HOME_CATEGORIES.get(category, [])
        self.form["allowed"] = names or None
        self.form["service"] = ""                 # jamais de prestation choisie automatiquement
        self.form["date"] = ""
        self.form["time"] = ""
        self.booking_category = category
        self.booking_service_expanded = False
        self.show_page("booking")

    def book_service_direct(self, name: str):
        # Même si la cliente vient de cliquer sur une prestation, elle doit
        # confirmer son choix dans l'écran de réservation.
        cat_key = next((cat for n, cat, _ in SERVICES if n == name), None)
        category_label = next((label for n, cat, label in SERVICES if n == name), None)
        self.form["allowed"] = [n for n, cat, _ in SERVICES if cat == cat_key] if cat_key else None
        self.form["service"] = ""
        self.form["date"] = ""
        self.form["time"] = ""
        self.booking_category = category_label
        self.booking_service_expanded = False
        self.show_page("booking")

    def start_booking_from_detail(self):
        self.book_service_direct(self.detail_service)

    # ======================================================================
    # CONFIRMATION D'UNE RÉSERVATION  (écrit dans Firebase)
    # ======================================================================
    def check_availability(self):
        """Étape 1 : validation du formulaire puis fenêtre « Créneau disponible »."""
        f = self.form
        if not f["service"]:
            self.toast.show("Choisissez d'abord une prestation")
            return
        if not f["date"] or not f["time"]:
            self.toast.show("Choisissez une date et une heure")
            return
        if not f["name"].strip() or not f["address"].strip() or not f["phone"].strip():
            self.toast.show("Renseignez votre nom, l'adresse et le numéro à appeler")
            return
        if len(digits(f["phone"])) < 8:
            self.toast.show("Le numéro de téléphone semble incomplet")
            return
        recap = T(f"{f['service']} · {format_date_long(f['date'])} à {f['time']}\n{f['address']}", 12, INK)
        self.modal.open(ft.Column([
            ft.Container(width=38, height=4, bgcolor="#dddddd", border_radius=5),
            kicker("Planning intelligent"),
            T("Créneau disponible", 29, INK, font=SERIF),
            recap,
            T("Dans la version connectée, FIASI vérifiera les agendas, le temps de trajet et les autres "
              "prestations. Le numéro indiqué sera utilisé pour vous joindre lors du rendez-vous.", 13, MUTED),
            btn("Confirmer la réservation", lambda e: self._start_async(self.confirm_booking), bg=GOLD, fill=True),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    async def confirm_booking(self):
        """Étape 2 : création de la réservation dans /bookings + ligne d'activité."""
        f = self.form
        notes = f["notes"].strip()
        if f["extra"]:
            notes = (notes + "\n" if notes else "") + f"Prestation supplémentaire souhaitée : {f['extra']}"
        booking = Booking(
            id=new_booking_id(), name=f["name"].strip(), phone=f["phone"].strip(), service=f["service"],
            date=f["date"], time=f["time"], address=f["address"].strip(),
            notes=notes or "Aucune précision.", status="new",
        )
        try:
            await self.repo.create_booking(booking)                                   # <-- Firebase
            await self.repo.add_activity(f"Nouvelle réservation de {booking.name}")   # <-- journal
        except Exception as ex:
            self.modal.close()
            self.network_error_detail = str(ex)
            print("Erreur Firebase :", ex)
            self.show_page("offline")
            return

        self.modal.close()
        self.my_phone = f["phone"].strip()           # pour retrouver la réservation dans « Mes RDV »
        self._status_seen[booking.id] = booking.status
        self.form["notes"], self.form["extra"] = "", ""
        self.show_page("history")
        self.toast.show("Réservation confirmée")

    # ======================================================================
    # CATALOGUE D’IMAGES
    # ======================================================================
    def toggle_tryon_more(self):
        self.image_catalog_expanded = not getattr(self, "image_catalog_expanded", False)
        self.show_page("try")

    def set_tryon_catalog_category(self, category: str):
        self.image_catalog_category = category
        self.image_catalog_expanded = False
        self.show_page("try")

    # ======================================================================
    # MES RÉSERVATIONS (lecture Firebase)
    # ======================================================================
    def set_my_phone(self, value: str):
        """Appelé à chaque frappe dans le champ « Retrouver mes réservations »."""
        self.my_phone = value
        if len(digits(value)) >= 8:
            self._start_async(self.refresh_bookings)
        else:
            self.my_bookings = []
            self.fill_history()
            self.page.update()

    def fill_history(self):
        if self.history_list is None:
            return
        if self.my_bookings:
            self.history_list.controls = [history_card(b) for b in self.my_bookings]
        else:
            msg = ("Aucune réservation trouvée pour ce numéro." if len(digits(self.my_phone)) >= 8
                   else "Saisissez votre numéro pour voir vos réservations.")
            self.history_list.controls = [ft.Container(padding=pad_all(20), content=T(msg, 12, MUTED))]

    async def refresh_bookings(self):
        """Relit /bookings (filtré sur le numéro) et prévient la cliente si un statut a changé."""
        if len(digits(self.my_phone)) < 8:
            return
        try:
            fresh = await self.repo.list_bookings_for_phone(self.my_phone)
        except Exception as ex:
            print("Lecture Firebase impossible :", ex)
            return
        for b in fresh:
            old = self._status_seen.get(b.id)
            if old is not None and old != b.status:                 # la réception a modifié le statut
                self.toast.show(f"{b.service} : {CLIENT_STATUS_LABELS[b.status]}", 4)
            self._status_seen[b.id] = b.status
        self.my_bookings = fresh
        if self.current == "history":
            self.fill_history()
            self.page.update()

    async def poll_loop(self):
        """Tâche de fond : synchronisation automatique (équivalent du setInterval du HTML réception)."""
        try:
            while True:
                await asyncio.sleep(config.POLL_SECONDS)
                if len(digits(self.my_phone)) >= 8:
                    await self.refresh_bookings()
        except Exception:
            pass   # la session a été fermée
