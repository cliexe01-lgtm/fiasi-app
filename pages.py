"""
pages.py — Les 9 écrans de l'application CLIENTE FIASI.

Chaque fonction `page_xxx(app)` correspond à une <section class="page" id="xxx"> du HTML
et renvoie un contrôle Flet. `app` est l'instance de FiasiClient (voir app.py) : on s'en
sert pour naviguer (app.show_page), lire/écrire le formulaire (app.form), afficher un
toast, etc.

CORRESPONDANCE HTML -> FLET :
    <div class="...">      -> ft.Container / ft.Column / ft.Row
    flex / grid CSS        -> ft.Row / ft.Column (expand=True pour se partager la largeur)
    onclick="showPage()"   -> on_click=lambda e: app.show_page(...)
    <select>               -> ChoiceGroup (rangée de pastilles, voir fiasi_common/ui.py)
    <input type=date>      -> bande de 14 jours cliquables
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

import flet as ft

from fiasi_common.models import (
    CATALOG_FILTERS, CLIENT_STATUS_LABELS, EXTRAS, SERVICES, STATUS_LABELS,
    TIME_SLOTS, DAYS_FR, MONTHS_FR, format_date_long,
)
from inspiration_catalog import CATALOG

from fiasi_common.ui import (
    BLACK, BOLD, CENTER, CENTER_LEFT, CREAM, FIT_CONTAIN, FIT_COVER, GOLD, GOLD2, INK, LINE,
    MUTED, SERIF, WHITE, XBOLD, ChoiceGroup, T, border, border_bottom, btn, circle, margin,
    pad, pad_all, pad_hv, radius,
)

# Style commun des champs de saisie (équivalent de .field input en CSS)
TF_STYLE = dict(
    border_radius=3, border_color=LINE, focused_border_color=GOLD, text_size=14,
    content_padding=pad_hv(13, 13), bgcolor=WHITE,
)


# ===========================================================================
# BRIQUES RÉUTILISABLES
# ===========================================================================
def logo(width):
    """Logo FIASI (assets/logo.png). Le HTML l'intégrait en base64 dans la page."""
    return ft.Image(src="logo.png", width=width, fit=FIT_CONTAIN)


def pattern_strip(height=24):
    """Bandeau doré à losanges (classe CSS .pattern-strip)."""
    return ft.Container(
        height=height, bgcolor=GOLD, alignment=CENTER_LEFT, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=T("◆ ◇ " * 60, height * 0.5, "#16120e", no_wrap=True, overflow=ft.TextOverflow.CLIP),
    )


def pattern_label(text="Héritage · Élégance · Beauté"):
    return ft.Container(content=T(text.upper(), 8, GOLD, ls=1.8), alignment=CENTER, padding=pad_hv(0, 6))


def afro_line():
    """Ligne de losanges décorative (classe CSS .afro-line)."""
    return ft.Container(content=T("◆ ◇ ◆ ◇ ◆", 8, GOLD, ls=5), alignment=CENTER, padding=pad_hv(0, 4))


def scroll_page(controls, bottom=92):
    """
    Colonne scrollable. `bottom` laisse la place à la barre de navigation du bas
    (padding-bottom:92px dans le CSS).
    """
    return ft.Column(controls=list(controls) + [ft.Container(height=bottom)],
                     scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


def header(title, back=None, right=None):
    """En-tête blanc avec bouton retour ‹ (classe CSS .header)."""
    left = circle("‹", back, bg="#f5f2ed", border_color=None, font=20) if back else ft.Container(width=38)
    return ft.Container(
        height=70, padding=pad_hv(18, 15), bgcolor=WHITE, border=border_bottom(),
        content=ft.Row([left, T(title, 23, INK, font=SERIF), right or ft.Container(width=38)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def kicker(text, color=GOLD):
    return T(text.upper(), 10, color, ls=2.3)


def labeled(label, control, note=None):
    """Étiquette en petites capitales au-dessus d'un champ (.field label)."""
    items = [T(label.upper(), 10, INK, ls=1.2), control]
    if note:
        items.append(T(note, 10, "#888888"))
    return ft.Column(items, spacing=7)


# ===========================================================================
# 1) ACCUEIL
# ===========================================================================
def quick_card(num, title, sub, on_click):
    """Carte de raccourci (.quick.afro-tribal) : fond crème + frise dorée en bas."""
    return ft.Container(
        expand=True, height=118, bgcolor="#fbf9f5", border=border(1, "#e2d8c8"),
        on_click=on_click, ink=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Stack([
            ft.Container(padding=pad_all(15), content=ft.Column(
                [T(num, 10, MUTED), T(title, 20, INK, font=SERIF), T(sub, 10, MUTED)], spacing=5)),
            ft.Container(right=10, top=8, content=T("◇", 16, GOLD)),
            ft.Container(left=0, right=0, bottom=0, height=11, bgcolor=GOLD,
                         content=T("◆ " * 60, 7, "#17120d", no_wrap=True, overflow=ft.TextOverflow.CLIP)),
        ]),
    )


def page_home(app):
    brand = ft.Container(
        padding=pad(18, 12, 18, 4),
        content=ft.Row([logo(92), ft.Container(width=38)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )

    # Grande carte d'accueil sombre (.welcome.afro-weave.afro-corner)
    welcome = ft.Container(
        margin=margin(16, 8, 16, 12), padding=pad(17, 18, 17, 18), border_radius=radius(6),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                                   colors=["#15110d", "#2b2014", "#15110d"]),
        content=ft.Stack([
            ft.Column([
                kicker("FIASI · Beauty at home"),
                ft.Container(height=6),
                T("Votre beauté,", 34, WHITE, font=SERIF),
                T("chez vous.", 34, WHITE, font=SERIF, italic=True),
                ft.Container(width=265, padding=pad_hv(0, 12),
                             content=T("Coiffure, soins, maquillage et ongles à domicile.", 12, "#d0d0d0")),
                btn("Réserver une prestation", lambda e: app.open_category("Coiffure"), bg=GOLD, rad=3),
            ], spacing=0),
            ft.Container(right=0, top=-4, content=T("◆", 18, GOLD)),
            ft.Container(left=0, bottom=-4, content=T("◇", 15, GOLD)),
        ]),
    )

    quick = ft.Column([
        ft.Row([quick_card("01", "Coiffure", "Braids · soins", lambda e: app.open_category("Coiffure")),
                quick_card("02", "Esthétique", "Visage · soins", lambda e: app.open_category("Esthétique"))], spacing=9),
        ft.Row([quick_card("03", "Ongles", "Manucure · pédicure", lambda e: app.open_category("Ongles")),
                quick_card("04", "Maquillage", "Jour · soirée", lambda e: app.open_category("Maquillage"))], spacing=9),
        ft.Row([
            btn("✦ Catalogue d’images", lambda e: app.show_page("try"), bg=WHITE, fg=INK, size=11,
                border_color="#ddd6cb", expand=True, rad=0),
        ], spacing=9),
    ], spacing=9)

    section = ft.Container(padding=pad(16, 10, 16, 20), content=ft.Column([
        ft.Row([T("Que voulez-vous faire ?", 22, INK, font=SERIF),
                ft.Container(content=T("Tout voir", 12, GOLD, BOLD), on_click=lambda e: app.show_page("catalogue"))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        quick,
    ], spacing=12))

    return scroll_page([brand, pattern_strip(), pattern_label(), welcome, section,
                        afro_line(), pattern_strip()], bottom=82)


# ===========================================================================
# 2) CATALOGUE  (+ bloc animé « Comment ça marche ? »)
# ===========================================================================
class Whiteboard:
    """
    Reproduit l'animation CSS @keyframes wbStep : 3 étapes qui défilent toutes les 4 s
    avec une barre de progression. Une tâche asynchrone (run) fait avancer l'étape ;
    elle s'arrête d'elle-même quand l'utilisatrice quitte le catalogue.
    """
    STEPS = [
        ("①", "Choisissez votre prestation", "Tresses, perruque, tissage, soins, ongles…"),
        ("②", "Réservez votre créneau", "Date, heure, adresse et numéro pour vous joindre."),
        ("③", "FIASI vous appelle", "On précise le modèle, les besoins et le prix avant l'intervention."),
    ]

    def __init__(self):
        self.i = 0
        self.icon = T("", 30, INK)
        self.title = T("", 13, INK, XBOLD)
        self.sub = T("", 10, MUTED)
        self.stage = ft.Container(
            height=142, bgcolor="#fffdf8", alignment=CENTER, padding=pad_hv(16, 0),
            opacity=1, animate_opacity=250,                      # fondu entre les étapes
            content=ft.Column([self.icon, self.title, self.sub], spacing=6,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                              alignment=ft.MainAxisAlignment.CENTER),
        )
        self.bar = ft.ProgressBar(value=1 / 3, color=BLACK, bgcolor="#eeeeee", height=3)
        self.control = ft.Container(
            margin=margin(16, 0, 16, 18), bgcolor=WHITE, border=border(), border_radius=radius(16),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column([
                ft.Container(padding=pad_hv(14, 12), border=border_bottom(), content=ft.Row(
                    [T("Comment ça marche ?", 12, INK, BOLD), T("30 sec", 10, MUTED)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
                self.stage, self.bar,
            ], spacing=0),
        )
        self._paint()

    def _paint(self):
        icon, title, sub = self.STEPS[self.i]
        self.icon.value, self.title.value, self.sub.value = icon, title, sub
        self.bar.value = (self.i + 1) / 3

    async def run(self, app):
        try:
            while app.current == "catalogue" and app.wb is self:
                await asyncio.sleep(4)
                if app.current != "catalogue" or app.wb is not self:
                    break
                self.stage.opacity = 0                 # fondu sortant
                app.page.update()
                await asyncio.sleep(0.28)
                self.i = (self.i + 1) % 3
                self._paint()
                self.stage.opacity = 1                 # fondu entrant
                app.page.update()
        except Exception:
            pass  # la page a été fermée pendant l'animation


def service_line(app, name, cat_label):
    """Une ligne du catalogue (.service-line). Toucher le nom ouvre la fiche, le bouton réserve."""
    return ft.Container(
        padding=pad_hv(14, 14), bgcolor=WHITE, border=border(), border_radius=radius(14),
        content=ft.Row([
            ft.Container(expand=True, on_click=lambda e, n=name: app.open_detail(n),
                         content=ft.Column([T(name, 14, INK, XBOLD), T(cat_label, 10, MUTED)], spacing=3)),
            btn("Réserver", lambda e, n=name: app.book_service_direct(n), size=10, rad=9,
                padding=pad_hv(12, 9), weight=XBOLD),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def page_catalogue(app):
    """Catalogue : 3 prestations principales par catégorie, puis un bouton « Autres »."""
    featured = {
        "coiffure": ["Tresses africaines", "Pose de perruque", "Tissage ouvert"],
        "esthetique": ["Soin du visage classique", "Massage relaxant", "Épilation sourcils"],
        "ongles": ["Manucure classique", "Pédicure classique", "Vernis semi-permanent"],
        "maquillage": ["Maquillage naturel", "Maquillage soirée", "Maquillage mariage"],
    }
    labels = {"coiffure":"Coiffure", "esthetique":"Esthétique", "ongles":"Onglerie", "maquillage":"Maquillage"}
    selected = app.cat_filter
    keys = ["coiffure", "esthetique", "ongles", "maquillage"] if selected == "all" else [selected]

    # État indépendant pour chaque catégorie : « Autres » n'ouvre que cette catégorie.
    expanded = getattr(app, "catalog_expanded_categories", set())
    if not isinstance(expanded, set):
        expanded = set()

    def toggle_category(key):
        if key in expanded:
            expanded.remove(key)
        else:
            expanded.add(key)
        app.catalog_expanded_categories = expanded
        # Reconstruit proprement la page : aucune méthode `refresh()`
        # inexistante n'est appelée. Cela corrige « Object has no attribute… ».
        app.show_page("catalogue")

    controls = []
    for key in keys:
        label = labels[key]
        names = [n for n, k, _ in SERVICES if k == key]
        top_names = [n for n in featured[key] if n in names]
        rest = sorted([n for n in names if n not in top_names], key=lambda x: x.casefold())
        visible = top_names + (rest if key in expanded else [])
        more_text = "Masquer les autres" if key in expanded else "Autres prestations"

        section_controls = [
            ft.Row([
                T(label, 21, INK, font=SERIF),
                T(f"{len(names)} prestations", 10, MUTED),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Column([service_line(app, n, label) for n in visible], spacing=8),
        ]
        if rest:
            section_controls.append(
                btn(more_text, lambda e, k=key: toggle_category(k),
                    bg=WHITE, fg=INK, border_color=LINE, fill=True)
            )
        controls.append(ft.Container(
            padding=pad(16, 4, 16, 10),
            content=ft.Column(section_controls, spacing=9),
        ))

    return scroll_page([
        header("Nos prestations", back=lambda e: app.show_page("home")),
        pattern_strip(),
        ft.Container(padding=pad_hv(16, 14), content=ft.Column([
            kicker("Catalogue FIASI"),
            T("Les prestations principales d'abord", 28, INK, font=SERIF),
            T("Trois prestations principales sont affichées en priorité. Utilisez « Autres prestations » pour voir le reste, classé alphabétiquement.", 12, MUTED),
            ChoiceGroup(CATALOG_FILTERS, app.cat_filter, on_change=app.set_cat_filter, scroll=True).control,
        ], spacing=9)),
        *controls,
    ])


# ===========================================================================
# 3) DÉTAIL D'UNE PRESTATION
# ===========================================================================
def gallery_item(url, title):
    return ft.Container(
        expand=True, height=145, border_radius=radius(4), border=border(1, "#e3dacd"), bgcolor="#e8dfd1",
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Stack([
            # Image distante (Pexels). error_content = repli si pas de réseau.
            ft.Image(src=url, width=400, height=145, fit=FIT_COVER,
                     error_content=ft.Container(alignment=CENTER, content=T("Photo indisponible", 10, MUTED))),
            ft.Container(left=9, bottom=8, content=T(title, 12, WHITE, BOLD)),
        ]),
    )


def page_detail(app):
    name = app.detail_service
    cat_label = next((cat for n, _, cat in SERVICES if n == name), "Beauté")
    banner = ft.Container(
        height=310, alignment=CENTER, padding=pad_all(20),
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#151515", "#aa885b"]),
        content=T(name.upper(), 32, WHITE, font=SERIF),
    )
    body = ft.Container(padding=pad_hv(18, 20), content=ft.Column([
        kicker(f"{cat_label} à domicile"),
        ft.Row([T(name, 29, INK, font=SERIF, expand=True), T("Sur devis", 14, INK, BOLD)],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        T("Une prestation réalisée chez vous par une professionnelle sélectionnée selon sa "
          "disponibilité, sa proximité et son expertise.", 13, MUTED),
        ft.Row([ft.Container(content=T(t, 11, INK), bgcolor=CREAM, padding=pad_hv(10, 8))
                for t in ("★ 4.9", "~3h30", "À domicile")], spacing=7),
        btn("Réserver cette prestation", lambda e: app.start_booking_from_detail(), bg=BLACK, fill=True),
                afro_line(),
        T("Exemples de rendu", 20, INK, font=SERIF),
        ft.Row([
            gallery_item("assets/catalog/hair_01.png", "Exemple coiffure"),
            gallery_item("assets/catalog/wig_01.png", "Exemple perruque"),
        ], spacing=9),
    ], spacing=14))
    return scroll_page([
        header("Prestation", back=lambda e: app.back_page(),
               right=circle("♡", lambda e: app.toast.show("Ajouté aux favoris"))),
        pattern_strip(), banner, body,
    ])


# ===========================================================================
 # 4) CATALOGUE D’IMAGES
# ===========================================================================
def apply_hair(hair: ft.Container, style: str):
    """
    Dessine la coiffure : un grand contour sombre autour du visage.
    ('' = classique, 'long' = plus longue, 'braids' = contour plus fin et plus brun)
    """
    if style == "long":
        hair.height = 300
        hair.border = border(25, "#111111")
        hair.border_radius = ft.BorderRadius(top_left=95, top_right=95, bottom_left=38, bottom_right=38)
    elif style == "braids":
        hair.height = 245
        hair.border = border(17, "#2a2018")
        hair.border_radius = ft.BorderRadius(top_left=95, top_right=95, bottom_left=66, bottom_right=66)
    else:
        hair.height = 245
        hair.border = border(25, "#111111")
        hair.border_radius = ft.BorderRadius(top_left=95, top_right=95, bottom_left=66, bottom_right=66)


def image_catalog_card(item, category):
    """Carte photo simple du catalogue."""
    image = ft.Image(
        src=("assets/" + item["image"]), width=174, height=190, fit=FIT_COVER,
        error_content=ft.Container(
            width=174, height=190, bgcolor="#eee9e1", alignment=CENTER,
            content=T("Image indisponible", 10, MUTED),
        ),
    )
    return ft.Container(
        width=182, bgcolor=WHITE, border=border(1, LINE), border_radius=radius(12),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Column([
            image,
            ft.Container(padding=pad_hv(9, 8), content=T(item["name"], 12, INK, BOLD, max_lines=2)),
        ], spacing=0),
    )


def _catalogue_category_card(app, category, title, subtitle, image_src):
    """Une couverture qui ouvre le catalogue complet de la catégorie."""
    return ft.Container(
        expand=True, height=210, bgcolor=WHITE, border=border(1, LINE),
        border_radius=radius(14), clip_behavior=ft.ClipBehavior.HARD_EDGE,
        on_click=lambda e, c=category: app.set_tryon_catalog_category(c), ink=True,
        content=ft.Column([
            ft.Image(src=image_src, width=205, height=145, fit=FIT_COVER,
                     error_content=ft.Container(width=205, height=145, bgcolor="#eee9e1",
                                                alignment=CENTER, content=T("Photo indisponible", 10, MUTED))),
            ft.Container(padding=pad_hv(10, 7), content=ft.Column([
                T(title, 14, INK, BOLD), T(subtitle, 10, MUTED),
            ], spacing=2)),
        ], spacing=0),
    )


def page_try(app):
    """Catalogue d'images FIASI : une page d'accueil puis une galerie par catégorie."""
    category = getattr(app, "image_catalog_category", "")

    cover = {
        "Coiffure & tresses": "assets/catalog/hair_01.png",
        "Perruques": "assets/catalog/wig_01.png",
        "Onglerie": "assets/catalog/nail_01.png",
        "Maquillage": "assets/catalog/makeup_01.png",
    }

    if not category:
        category_cards = ft.Column([
            ft.Row([
                _catalogue_category_card(app, "Coiffure & tresses", "Coiffures & tresses", "Tresses, braids, twists…", cover["Coiffure & tresses"]),
                _catalogue_category_card(app, "Perruques", "Perruques", "Lace, bob, curly, wave…", cover["Perruques"]),
            ], spacing=9),
            ft.Row([
                _catalogue_category_card(app, "Onglerie", "Onglerie", "Manucure, nail art…", cover["Onglerie"]),
                _catalogue_category_card(app, "Maquillage", "Maquillage", "Naturel, glam, mariage…", cover["Maquillage"]),
            ], spacing=9),
        ], spacing=9)
        return scroll_page([
            header("Catalogue d’images", back=lambda e: app.back_page()),
            pattern_strip(),
            ft.Container(padding=pad_hv(16, 14), content=ft.Column([
                kicker("CATALOGUE FIASI"),
                T("Trouvez votre inspiration", 29, INK, font=SERIF),
                T("Choisissez une catégorie pour découvrir de nombreux modèles en photos.", 12, MUTED),
                category_cards,
            ], spacing=12)),
        ])

    items = CATALOG[category]
    expanded = getattr(app, "image_catalog_expanded", False)
    featured_names = {
        "Coiffure & tresses": ["Box braids", "Cornrows", "Knotless braids", "Goddess braids", "Fulani braids", "Stitch braids"],
        "Perruques": ["Afro wig", "Bob droit", "Bob bouclé", "Body wave", "Glueless wig", "Deep wave"],
        "Onglerie": ["Baby boomer", "French classique", "Manucure classique", "Chrome doré", "Nude", "Cat eye"],
        "Maquillage": ["Maquillage naturel", "Maquillage soirée", "Maquillage mariage", "Soft glam", "Golden glam", "Red lips"],
    }[category]
    top = [x for x in items if x["name"] in featured_names]
    rest = sorted([x for x in items if x not in top], key=lambda x: x["name"].lower())
    shown = top + (rest if expanded else [])

    grid = ft.GridView(expand=False, runs_count=2, max_extent=185,
                       child_aspect_ratio=0.82, spacing=9, run_spacing=9)
    for item in shown:
        grid.controls.append(image_catalog_card(item, category))

    return scroll_page([
        header(category, back=lambda e: app.set_tryon_catalog_category("")),
        pattern_strip(),
        ft.Container(padding=pad_hv(16, 14), content=ft.Column([
            kicker("CATALOGUE D’IMAGES"),
            T(category, 27, INK, font=SERIF),
            T(f"{len(items)} modèles disponibles", 12, MUTED),
            grid,
            btn("Voir encore plus d’images" if not expanded else "Réduire les images",
                lambda e: app.toggle_tryon_more(), bg=WHITE, fg=INK,
                border_color=LINE, fill=True),
        ], spacing=10)),
    ])


# ===========================================================================
# 5) RÉSERVATION
# ===========================================================================
def step_dot(n, label, active):
    return ft.Column([
        ft.Container(width=27, height=27, alignment=CENTER, border_radius=radius(14),
                     bgcolor=BLACK if active else "#eeeeee", content=T(n, 11, WHITE if active else "#aaaaaa", BOLD)),
        T(label, 10, INK if active else "#aaaaaa"),
    ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def page_booking(app):
    f = app.form

    def setter(key):
        return lambda e: f.__setitem__(key, e.control.value)

    # La réservation ne choisit jamais automatiquement une prestation.
    # On affiche seulement 3 choix principaux + « Autres prestations ».
    category = getattr(app, "booking_category", None)
    category_key = next((k for k, label in {
        "coiffure": "Coiffure", "esthetique": "Esthétique",
        "ongles": "Onglerie", "maquillage": "Maquillage"
    }.items() if label == category), None)
    allowed = f.get("allowed") or []

    featured = {
        "coiffure": ["Tresses africaines", "Pose de perruque", "Tissage ouvert"],
        "esthetique": ["Soin du visage classique", "Massage relaxant", "Épilation sourcils"],
        "ongles": ["Manucure classique", "Pédicure classique", "Vernis semi-permanent"],
        "maquillage": ["Maquillage naturel", "Maquillage soirée", "Maquillage mariage"],
    }
    label_by_key = {"coiffure":"Coiffure", "esthetique":"Esthétique", "ongles":"Onglerie", "maquillage":"Maquillage"}

    if category_key:
        names = [n for n, k, _ in SERVICES if k == category_key]
    elif allowed:
        names = list(allowed)
    else:
        names = [n for n, _, _ in SERVICES]

    top_names = [n for n in featured.get(category_key, []) if n in names]
    rest = sorted([n for n in names if n not in top_names], key=lambda x: x.casefold())
    expanded = getattr(app, "booking_service_expanded", False)

    service_options = [(n, n) for n in top_names]
    if rest:
        service_options.append(("__other__", "Autres"))
    if expanded:
        service_options = [(n, n) for n in top_names + rest]

    def choose_service(value):
        if value == "__other__":
            app.booking_service_expanded = True
            app.show_page("booking")
            return
        f["service"] = value
        app.page.update()

    service_group = ChoiceGroup(
        service_options,
        f.get("service") or None,
        on_change=choose_service,
        scroll=False,
        size=11,
        rad=12,
    )

    def show_all_services(_):
        app.booking_service_expanded = True
        app.show_page("booking")

    def hide_all_services(_):
        app.booking_service_expanded = False
        app.show_page("booking")

    if expanded:
        service_hint = f"Toutes les prestations {label_by_key.get(category_key, '')} — classées alphabétiquement"
        other_button = btn("Voir moins", hide_all_services, bg=WHITE, fg=INK, border_color=LINE, fill=True)
    else:
        service_hint = "Choisissez une prestation. Trois choix principaux sont affichés pour garder l'écran simple."
        other_button = btn("Autres prestations", show_all_services,
                           bg=WHITE, fg=INK, border_color=LINE, fill=True) if rest else None

    service_box_controls = [
        T("Choisissez votre prestation", 10, INK, BOLD),
        service_group.control,
        T(service_hint, 10, MUTED),
    ]
    if other_button:
        service_box_controls.append(other_button)
    service_box = ft.Container(
        padding=pad_hv(14, 12), bgcolor=CREAM, border_radius=radius(10),
        content=ft.Column(service_box_controls, spacing=9),
    )

    today = date.today()
    days = [today + timedelta(days=i) for i in range(14)]
    date_group = ChoiceGroup(
        [(d.isoformat(), f"{DAYS_FR[d.weekday()]}\n{d.day:02d}\n{MONTHS_FR[d.month - 1]}") for d in days],
        f.get("date") or None, on_change=lambda v: f.__setitem__("date", v), scroll=True, rad=10)
    time_group = ChoiceGroup(
        [(t, t) for t in TIME_SLOTS], f.get("time") or None,
        on_change=lambda v: f.__setitem__("time", v))

    form = ft.Container(padding=pad_hv(16, 18), content=ft.Column([
        labeled("Votre nom", ft.TextField(value=f["name"], hint_text="Prénom Nom", on_change=setter("name"), **TF_STYLE)),
        labeled("Prestation", service_box,
                 note="Le prix n'est pas fixe. Nous vous appelons après la réservation pour préciser le modèle, vos besoins et vous communiquer le tarif."),
        labeled("Date", date_group.control),
        labeled("Heure souhaitée", time_group.control),
        labeled("Adresse", ft.TextField(value=f["address"], hint_text="Quartier, rue, repère...", on_change=setter("address"), **TF_STYLE)),
        labeled("Numéro à appeler",
                ft.TextField(value=f["phone"], hint_text="+228 XX XX XX XX", keyboard_type=ft.KeyboardType.PHONE,
                             on_change=setter("phone"), **TF_STYLE),
                note="Ce numéro servira à vous appeler pour confirmer le rendez-vous et lorsque la professionnelle sera sur place."),
        labeled("Précisions (modèle, longueur…)",
                ft.TextField(value=f["notes"], hint_text="Facultatif", multiline=True, min_lines=2, max_lines=4,
                             on_change=setter("notes"), **TF_STYLE)),
    ], spacing=16))

    summary = ft.Container(margin=margin(16, 0, 16, 0), padding=pad_all(16), bgcolor=CREAM, content=ft.Column([
        T("Total estimé", 12, INK),
        T("Prix communiqué par téléphone", 18, INK, font=SERIF),
        btn("Vérifier la disponibilité", lambda e: app.check_availability(), bg=GOLD, fill=True),
    ], spacing=10))

    steps = ft.Container(padding=pad_hv(20, 18), content=ft.Row(
        [step_dot("1", "Service", bool(f.get("service"))), step_dot("2", "Date", bool(f.get("date"))),
         step_dot("3", "Adresse", bool(f.get("address"))), step_dot("4", "Confirmation", False)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    return scroll_page([header("Réserver", back=lambda e: app.back_page()), pattern_strip(), steps, form, summary])


# ===========================================================================
# 6) ERREUR DE CONNEXION
# ===========================================================================
def page_offline(app):
    detail = getattr(app, "network_error_detail", "")
    return scroll_page([
        header("Connexion nécessaire", back=lambda e: app.show_page("home")),
        pattern_strip(),
        ft.Container(
            padding=pad(22, 28, 22, 40),
            content=ft.Column([
                T("Connexion Internet indisponible", 29, INK, font=SERIF),
                T("Votre réservation n'a pas été envoyée.", 14, INK, BOLD),
                T("Vérifiez votre connexion Internet puis réessayez. Votre formulaire n'a pas besoin d'être recréé : revenez simplement à la réservation.", 13, MUTED),
                ft.Container(height=8),
                btn("Retour à la réservation", lambda e: app.show_page("booking"), bg=GOLD, fill=True),
                btn("Retour à l'accueil", lambda e: app.show_page("home"), bg=WHITE, fg=INK, border_color=LINE, fill=True),
                ft.Container(height=8),
                T("Détail technique (facultatif)", 10, MUTED, BOLD),
                T(detail[:500] if detail else "Aucun détail disponible.", 10, MUTED),
            ], spacing=12),
        ),
    ])


# ===========================================================================
# 6) MES RÉSERVATIONS
# ===========================================================================
# ===========================================================================
def history_card(b):
    """Une réservation de la cliente, avec son statut mis à jour par la réception."""
    _, bg, fg = STATUS_LABELS[b.status]
    pill = ft.Container(content=T(CLIENT_STATUS_LABELS[b.status], 9, fg, BOLD), bgcolor=bg, padding=pad_hv(8, 5))
    lines = [
        ft.Row([T(b.service, 20, INK, font=SERIF, expand=True), pill],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
        T(f"{format_date_long(b.date)} · {b.time} · {b.address}", 11, MUTED),
    ]
    if b.pro and b.pro not in ("À attribuer", "—"):
        lines.append(T(f"Professionnelle : {b.pro}", 11, INK, BOLD))
    lines.append(T(f"{b.id} · Prix communiqué par téléphone", 11, INK, BOLD))
    return ft.Container(margin=margin(16, 10, 16, 0), padding=pad_all(16), border=border(),
                        content=ft.Column(lines, spacing=7))


def page_history(app):
    app.history_list = ft.Column(spacing=0)
    app.fill_history()
    phone = ft.TextField(value=app.my_phone, hint_text="Votre numéro (+228 …)", keyboard_type=ft.KeyboardType.PHONE,
                         on_change=lambda e: app.set_my_phone(e.control.value), **TF_STYLE)
    finder = ft.Container(padding=pad(16, 14, 16, 4), content=labeled(
        "Retrouver mes réservations", phone,
        note="Entrez le numéro utilisé lors de la réservation. Le statut se met à jour automatiquement."))
    empty = ft.Container(padding=pad_hv(25, 45), alignment=CENTER, content=ft.Column([
        T("Besoin d'une nouvelle beauté ?", 25, INK, font=SERIF),
        btn("Explorer le catalogue", lambda e: app.show_page("catalogue"), bg=BLACK),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    return scroll_page([header("Mes réservations", back=lambda e: app.show_page("home")),
                        finder, app.history_list, empty])

PAGES = {
    "home": page_home, "catalogue": page_catalogue, "detail": page_detail, "try": page_try,
    "booking": page_booking, "offline": page_offline, "history": page_history,
}
