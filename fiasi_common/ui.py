"""
ui.py — Petits composants Flet partagés par les deux applications.

CHOIX DE CONCEPTION (important pour la compatibilité) :
  Flet 0.80.x (la série "1.0") a renommé plusieurs API (Dropdown.on_change -> on_select,
  ft.padding.all -> ft.Padding.all, ElevatedButton -> Button, page.dialog -> page.show_dialog…).
  Pour que le code reste robuste, on s'appuie uniquement sur les briques les plus stables :
      Container, Row, Column, Stack, Text, TextField, Image
  et on reconstruit nous-mêmes :
      - les boutons       -> btn()          (Container cliquable)
      - les listes déroul.-> ChoiceGroup    (rangée de "pastilles")
      - les pop-up        -> Modal          (calque dans un Stack)
      - les snackbars     -> Toast          (calque dans un Stack)
  Les marges / bordures sont créées via les constructeurs (ft.Padding(left=…)),
  identiques dans toutes les versions.
"""
from __future__ import annotations

import asyncio
import inspect

import flet as ft

# ---------------------------------------------------------------------------
# PALETTE (variables CSS :root du HTML d'origine)
# ---------------------------------------------------------------------------
BLACK = "#0b0b0b"
INK = "#161616"
GOLD = "#b28a50"
GOLD2 = "#d5b477"
CREAM = "#f5f0e8"
LINE = "#e8e2d8"
MUTED = "#777777"
DANGER = "#b33a32"
WHITE = "#ffffff"
SERIF = "Georgia"            # police des titres (repli automatique si absente)

BOLD = ft.FontWeight.BOLD
XBOLD = ft.FontWeight.W_800

# Alignements fréquents (x, y entre -1 et 1)
CENTER = ft.Alignment(0, 0)
CENTER_LEFT = ft.Alignment(-1, 0)

# Compatibilité : ImageFit (anciennes versions) est devenu BoxFit (1.0)
_FIT = getattr(ft, "BoxFit", None) or getattr(ft, "ImageFit")
FIT_COVER = _FIT.COVER
FIT_CONTAIN = _FIT.CONTAIN


# ---------------------------------------------------------------------------
# PETITES FONCTIONS DE MISE EN FORME (padding, marges, bordures)
# ---------------------------------------------------------------------------
def pad(l=0, t=0, r=0, b=0):
    return ft.Padding(left=l, top=t, right=r, bottom=b)


def pad_all(v):
    return pad(v, v, v, v)


def pad_hv(h, v):
    """h = horizontal (gauche+droite), v = vertical (haut+bas)."""
    return pad(h, v, h, v)


def margin(l=0, t=0, r=0, b=0):
    return ft.Margin(left=l, top=t, right=r, bottom=b)


def border(width=1, color=LINE):
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def border_bottom(width=1, color=LINE):
    return ft.Border(bottom=ft.BorderSide(width, color))


def radius(v):
    return ft.BorderRadius(top_left=v, top_right=v, bottom_left=v, bottom_right=v)


def radius_top(v):
    return ft.BorderRadius(top_left=v, top_right=v, bottom_left=0, bottom_right=0)


def scrim(opacity=0.5):
    """Noir semi-transparent pour fond de modale."""
    return ft.Colors.with_opacity(opacity, "#000000")


def initials(name: str) -> str:
    """'Afi Mensah' -> 'AM' (fonction initials() du JS)."""
    return "".join(w[0] for w in (name or "?").split()[:2]).upper() or "?"


async def maybe_await(value):
    """
    Certaines méthodes Flet sont synchrones dans une version et asynchrones dans une autre
    (ex: page.launch_url). Ce petit utilitaire fonctionne dans les deux cas.
    """
    if inspect.isawaitable(value):
        return await value
    return value


# ---------------------------------------------------------------------------
# TEXTE
# ---------------------------------------------------------------------------
def T(value, size=12, color=INK, weight=None, font=None, italic=False, ls=None, **kw):
    """
    Raccourci pour ft.Text.
      italic -> italique ; ls -> espacement des lettres (letter-spacing CSS)
    """
    # Certaines versions de Flet n'exposent plus TextAlign de la même manière.
    # On retire donc cet ancien argument ici. Le centrage visuel est fait par
    # le Container/Column parent, ce qui évite toute erreur TextAlign.
    kw.pop("text_align", None)
    style = ft.TextStyle(italic=italic, letter_spacing=ls) if (italic or ls is not None) else None
    return ft.Text(str(value), size=size, color=color, weight=weight, font_family=font, style=style, **kw)


# ---------------------------------------------------------------------------
# BOUTONS (équivalents de .btn, .primary, .secondary, .circle…)
# ---------------------------------------------------------------------------
def btn(label, on_click, bg=BLACK, fg=WHITE, size=13, rad=3, padding=None,
        border_color=None, fill=False, expand=False, weight=BOLD):
    """
    Bouton rectangulaire.
      fill=True  -> occupe toute la largeur disponible (width:100% en CSS)
      expand=True-> se partage l'espace dans une Row
    """
    return ft.Container(
        content=T(label, size, fg, weight),
        alignment=CENTER if (fill or expand) else None,
        bgcolor=bg,
        border_radius=radius(rad),
        padding=padding or pad_hv(16, 13),
        border=border(1, border_color) if border_color else None,
        on_click=on_click,
        ink=True,
        expand=expand,
    )


def circle(label, on_click, size=38, bg=WHITE, border_color=LINE, fg=INK, font=18):
    """Bouton rond (retour ‹, favoris ♡, profil ◯…)."""
    return ft.Container(
        content=T(label, font, fg),
        width=size, height=size,
        alignment=CENTER,
        bgcolor=bg,
        border_radius=radius(size / 2),
        border=border(1, border_color) if border_color else None,
        on_click=on_click,
        ink=True,
    )


# ---------------------------------------------------------------------------
# CHOICE GROUP — remplace <select> et les chips
# ---------------------------------------------------------------------------
class ChoiceGroup:
    """
    Rangée de pastilles à sélection unique.

        g = ChoiceGroup([("a", "Option A"), ("b", "Option B")], value="a",
                        on_change=lambda v: print(v))
        page.add(g.control)      # g.value = valeur choisie

    scroll=True -> défilement horizontal sur une seule ligne (chips du catalogue)
    """

    def __init__(self, options, value=None, on_change=None, scroll=False, size=11,
                 active_bg=BLACK, active_fg=WHITE, rad=20):
        self.options = list(options)
        self.value = value
        self.on_change = on_change
        self.active_bg, self.active_fg = active_bg, active_fg
        self.pills = {}
        for val, label in self.options:
            self.pills[val] = ft.Container(
                content=T(label, size, INK),
                padding=pad_hv(13, 9),
                border_radius=radius(rad),
                on_click=lambda e, v=val: self.select(v),
                ink=True,
            )
        self.control = ft.Row(
            controls=list(self.pills.values()),
            wrap=not scroll,
            scroll=ft.ScrollMode.AUTO if scroll else None,
            spacing=7,
            run_spacing=7,
        )
        self._paint()

    def _paint(self):
        for val, pill in self.pills.items():
            on = val == self.value
            pill.bgcolor = self.active_bg if on else WHITE
            pill.border = border(1, self.active_bg if on else LINE)
            pill.content.color = self.active_fg if on else INK

    def select(self, value):
        self.value = value
        self._paint()
        self.control.update()
        if self.on_change:
            self.on_change(value)


# ---------------------------------------------------------------------------
# TOAST — remplace le <div class="toast"> et le SnackBar
# ---------------------------------------------------------------------------
class Toast:
    """
    Petit message temporaire. À placer dans le Stack racine : `stack.controls.append(toast.layer)`.
        toast.show("Réservation confirmée")
    """

    def __init__(self, page: ft.Page, bottom=90):
        self.page = page
        self._token = 0
        self.label = T("", 12, WHITE)
        self.box = ft.Container(content=self.label, bgcolor="#111111",
                                padding=pad_hv(16, 11), border_radius=radius(6), visible=False)
        # `bottom/left/right` positionnent le calque dans le Stack parent
        self.layer = ft.Container(content=ft.Row([self.box], alignment=ft.MainAxisAlignment.CENTER),
                                  bottom=bottom, left=0, right=0)

    def show(self, message: str, seconds: float = 2.4):
        """Peut être appelé depuis un gestionnaire normal (synchrone)."""
        _start_async(self.page, self._show, message, seconds)

    async def _show(self, message, seconds):
        self._token += 1
        mine = self._token          # si un autre toast arrive, l'ancien ne masque pas le nouveau
        self.label.value = message
        self.box.visible = True
        self.page.update()
        await asyncio.sleep(seconds)
        if mine == self._token:
            self.box.visible = False
            self.page.update()


# ---------------------------------------------------------------------------
# MODAL — remplace .overlay/.modal (réception) et .modal/.sheet (cliente)
# ---------------------------------------------------------------------------
class Modal:
    """
    Fenêtre superposée. À placer dans le Stack racine : `stack.controls.append(modal.layer)`.

        position="bottom" -> "bottom sheet" mobile, collée en bas, pleine largeur
        position="center" -> boîte centrée de largeur `width` (app réception)
    Un clic sur le fond sombre ferme la fenêtre.
    """

    def __init__(self, page: ft.Page, position="center", width=570, max_height=640):
        self.page = page
        self.position = position
        self.width = width
        self.max_height = max_height
        self.body = ft.Container()
        # on_click vide : empêche qu'un clic DANS la fenêtre remonte au fond et la ferme
        self.card = ft.Container(content=self.body, bgcolor=WHITE, on_click=lambda e: None)
        if position == "bottom":
            self.card.border_radius = radius_top(20)
            self.card.padding = pad(22, 22, 22, 28)
            inner = ft.Column([self.card], alignment=ft.MainAxisAlignment.END,
                              horizontal_alignment=ft.CrossAxisAlignment.STRETCH, expand=True)
        else:
            self.card.border_radius = radius(20)
            inner = ft.Row([self.card], alignment=ft.MainAxisAlignment.CENTER,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        # left/top/right/bottom=0 : le calque couvre tout le Stack parent (Positioned.fill)
        self.layer = ft.Container(content=inner, visible=False, left=0, top=0, right=0, bottom=0,
                                  bgcolor=scrim(0.5), padding=pad_all(0 if position == "bottom" else 20),
                                  on_click=lambda e: self.close())

    def open(self, content: ft.Control):
        self.body.content = content
        if self.position == "center":
            pw = self.page.width or 900
            ph = self.page.height or 800
            self.card.width = min(self.width, pw - 40)
            self.card.height = min(self.max_height, ph - 40)
        self.layer.visible = True
        self.page.update()

    def close(self):
        self.layer.visible = False
        self.page.update()


def configure_window(page: ft.Page, width=None, height=None, title=None):
    """Taille de fenêtre pour le test sur ordinateur (ignoré sur mobile/web)."""
    if title:
        page.title = title
    try:
        if width:
            page.window.width = width
        if height:
            page.window.height = height
    except Exception:
        pass  # API de fenêtre absente (web / mobile) : sans importance
