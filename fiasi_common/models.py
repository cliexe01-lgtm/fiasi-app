"""
models.py — Données métier FIASI (identiques pour l'app cliente et la réception).

Reprend les constantes qui étaient dispersées dans le JavaScript des deux fichiers HTML :
  - `labels`   (réception)  -> STATUS_LABELS
  - `staff`    (réception)  -> STAFF_SEED
  - liste des prestations   -> SERVICES
  - professionnelles (app cliente, page "Professionnelles") -> PROS_CLIENT
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# STATUTS D'UNE RÉSERVATION
# clé -> (libellé réception, couleur de fond, couleur du texte)
# (équivalent des classes CSS .s-new, .s-wait, … du HTML)
# ---------------------------------------------------------------------------
STATUS_LABELS = {
    "new":      ("Nouvelle",    "#f9e8e8", "#a33333"),
    "wait":     ("À confirmer", "#fff0da", "#9a641e"),
    "confirm":  ("Confirmée",   "#e7f1e9", "#39734d"),
    "assigned": ("Assignée",    "#e8eef5", "#456986"),
    "progress": ("En cours",    "#e7edf9", "#405c92"),
    "done":     ("Terminée",    "#ececec", "#555555"),
    "cancel":   ("Annulée",     "#eeeeee", "#8a5555"),
}

# Libellés vus par la CLIENTE (mêmes clés, vocabulaire adapté à la cliente).
CLIENT_STATUS_LABELS = {
    "new": "Envoyée",
    "wait": "À confirmer",
    "confirm": "Confirmée",
    "assigned": "Professionnelle assignée",
    "progress": "En cours chez vous",
    "done": "Terminée",
    "cancel": "Annulée",
}

DEFAULT_PRO = "À attribuer"

# ---------------------------------------------------------------------------
# PRESTATIONS (catalogue de l'app cliente) : (nom, clé de catégorie, libellé de catégorie)
# ---------------------------------------------------------------------------
SERVICES = [
    # COIFFURE
    ("Pose de perruque", "coiffure", "Coiffure"),
    ("Dépose de perruque", "coiffure", "Coiffure"),
    ("Pose de lace wig", "coiffure", "Coiffure"),
    ("Pose de closure", "coiffure", "Coiffure"),
    ("Pose de frontal", "coiffure", "Coiffure"),
    ("Tresses africaines", "coiffure", "Coiffure"),
    ("Box braids", "coiffure", "Coiffure"),
    ("Knotless braids", "coiffure", "Coiffure"),
    ("Fulani braids", "coiffure", "Coiffure"),
    ("Cornrows", "coiffure", "Coiffure"),
    ("Tribal braids", "coiffure", "Coiffure"),
    ("Passion twists", "coiffure", "Coiffure"),
    ("Senegalese twists", "coiffure", "Coiffure"),
    ("Vanilles", "coiffure", "Coiffure"),
    ("Nattes collées", "coiffure", "Coiffure"),
    ("Crochet braids", "coiffure", "Coiffure"),
    ("Tissage ouvert", "coiffure", "Coiffure"),
    ("Tissage fermé", "coiffure", "Coiffure"),
    ("Tissage avec closure", "coiffure", "Coiffure"),
    ("Tissage avec frontal", "coiffure", "Coiffure"),
    ("Défrisage", "coiffure", "Coiffure"),
    ("Coloration", "coiffure", "Coiffure"),
    ("Mèches / balayage", "coiffure", "Coiffure"),
    ("Brushing", "coiffure", "Coiffure"),
    ("Lissage", "coiffure", "Coiffure"),
    ("Boucles / mise en plis", "coiffure", "Coiffure"),
    ("Coiffure naturelle", "coiffure", "Coiffure"),
    ("Coiffure enfant", "coiffure", "Coiffure"),
    ("Coiffure événementielle", "coiffure", "Coiffure"),
    ("Chignon", "coiffure", "Coiffure"),
    ("Soin capillaire", "coiffure", "Coiffure"),
    ("Bain d'huile", "coiffure", "Coiffure"),
    ("Masque capillaire", "coiffure", "Coiffure"),
    ("Traitement cuir chevelu", "coiffure", "Coiffure"),
    ("Shampoing + soin", "coiffure", "Coiffure"),
    ("Coupe cheveux", "coiffure", "Coiffure"),
    ("Coupe pointes", "coiffure", "Coiffure"),
    ("Entretien des tresses", "coiffure", "Coiffure"),
    ("Entretien de perruque", "coiffure", "Coiffure"),
    ("Customisation de perruque", "coiffure", "Coiffure"),
    ("Lavage de perruque", "coiffure", "Coiffure"),
    ("Démêlage", "coiffure", "Coiffure"),

    # ESTHÉTIQUE / SOINS DU CORPS
    ("Soin du visage classique", "esthetique", "Esthétique"),
    ("Soin du visage profond", "esthetique", "Esthétique"),
    ("Nettoyage de peau", "esthetique", "Esthétique"),
    ("Gommage du visage", "esthetique", "Esthétique"),
    ("Masque visage", "esthetique", "Esthétique"),
    ("Hydratation visage", "esthetique", "Esthétique"),
    ("Soin anti-imperfections", "esthetique", "Esthétique"),
    ("Soin anti-âge", "esthetique", "Esthétique"),
    ("Soin contour des yeux", "esthetique", "Esthétique"),
    ("Soin des lèvres", "esthetique", "Esthétique"),
    ("Épilation sourcils", "esthetique", "Esthétique"),
    ("Épilation lèvre supérieure", "esthetique", "Esthétique"),
    ("Épilation menton", "esthetique", "Esthétique"),
    ("Épilation visage", "esthetique", "Esthétique"),
    ("Épilation aisselles", "esthetique", "Esthétique"),
    ("Épilation bras", "esthetique", "Esthétique"),
    ("Épilation jambes", "esthetique", "Esthétique"),
    ("Épilation maillot", "esthetique", "Esthétique"),
    ("Épilation corps complet", "esthetique", "Esthétique"),
    ("Gommage corps", "esthetique", "Esthétique"),
    ("Soin du dos", "esthetique", "Esthétique"),
    ("Soin des mains", "esthetique", "Esthétique"),
    ("Soin des pieds", "esthetique", "Esthétique"),
    ("Massage relaxant", "esthetique", "Esthétique"),
    ("Massage du dos", "esthetique", "Esthétique"),
    ("Massage jambes", "esthetique", "Esthétique"),
    ("Massage pieds", "esthetique", "Esthétique"),
    ("Massage aux huiles", "esthetique", "Esthétique"),
    ("Massage sportif", "esthetique", "Esthétique"),
    ("Massage prénatal", "esthetique", "Esthétique"),
    ("Massage crânien", "esthetique", "Esthétique"),
    ("Drainage esthétique", "esthetique", "Esthétique"),

    # ONGLERIE
    ("Manucure classique", "ongles", "Ongles"),
    ("Manucure express", "ongles", "Ongles"),
    ("Manucure russe", "ongles", "Ongles"),
    ("Manucure japonaise", "ongles", "Ongles"),
    ("Manucure spa", "ongles", "Ongles"),
    ("Beauté des mains", "ongles", "Ongles"),
    ("Vernis classique", "ongles", "Ongles"),
    ("Vernis semi-permanent", "ongles", "Ongles"),
    ("Dépose vernis semi-permanent", "ongles", "Ongles"),
    ("French manucure", "ongles", "Ongles"),
    ("Nail art", "ongles", "Ongles"),
    ("Pose capsules", "ongles", "Ongles"),
    ("Pose gel", "ongles", "Ongles"),
    ("Pose acrylique", "ongles", "Ongles"),
    ("Pose polygel", "ongles", "Ongles"),
    ("Gainage", "ongles", "Ongles"),
    ("Extension chablon", "ongles", "Ongles"),
    ("Remplissage gel", "ongles", "Ongles"),
    ("Dépose gel / acrylique", "ongles", "Ongles"),
    ("Pédicure classique", "ongles", "Ongles"),
    ("Pédicure spa", "ongles", "Ongles"),
    ("Pédicure médicale esthétique", "ongles", "Ongles"),
    ("Vernis semi-permanent pieds", "ongles", "Ongles"),
    ("French pieds", "ongles", "Ongles"),
    ("Soin des cuticules", "ongles", "Ongles"),
    ("Soin réparateur des ongles", "ongles", "Ongles"),
    ("Callosités / soin des talons", "ongles", "Ongles"),

    # MAQUILLAGE
    ("Maquillage naturel", "maquillage", "Maquillage"),
    ("Maquillage jour", "maquillage", "Maquillage"),
    ("Maquillage soirée", "maquillage", "Maquillage"),
    ("Maquillage événementiel", "maquillage", "Maquillage"),
    ("Maquillage mariage", "maquillage", "Maquillage"),
    ("Maquillage mariée", "maquillage", "Maquillage"),
    ("Maquillage invité mariage", "maquillage", "Maquillage"),
    ("Maquillage cérémonie", "maquillage", "Maquillage"),
    ("Maquillage anniversaire", "maquillage", "Maquillage"),
    ("Maquillage shooting photo", "maquillage", "Maquillage"),
    ("Maquillage vidéo", "maquillage", "Maquillage"),
    ("Maquillage artistique", "maquillage", "Maquillage"),
    ("Maquillage éditorial", "maquillage", "Maquillage"),
    ("Maquillage scène", "maquillage", "Maquillage"),
    ("Maquillage haute définition", "maquillage", "Maquillage"),
    ("Maquillage avec faux cils", "maquillage", "Maquillage"),
    ("Pose de faux cils", "maquillage", "Maquillage"),
    ("Retouche maquillage", "maquillage", "Maquillage"),
    ("Cours de maquillage", "maquillage", "Maquillage"),
    ("Conseil beauté / colorimétrie", "maquillage", "Maquillage"),
]


# Raccourcis de la page d'accueil -> prestations concernées (fonction openService() du JS)
HOME_CATEGORIES = {
    "Coiffure": [n for n, k, _ in SERVICES if k == "coiffure"],
    "Esthétique": [n for n, k, _ in SERVICES if k == "esthetique"],
    "Ongles": [n for n, k, _ in SERVICES if k == "ongles"],
    "Maquillage": [n for n, k, _ in SERVICES if k == "maquillage"],
}


# Filtres (chips) du catalogue : (clé, libellé)
CATALOG_FILTERS = [
    ("all", "Tout"), ("coiffure", "Coiffure"), ("esthetique", "Esthétique"),
    ("ongles", "Ongles"), ("maquillage", "Maquillage"),
]


TIME_SLOTS = ["07:00", "09:00", "11:00", "13:30", "16:00", "18:00"]

# Prestation supplémentaire (sans prix : le tarif est donné par téléphone)
EXTRAS = []

# ---------------------------------------------------------------------------
# ÉQUIPE (réception)
# ---------------------------------------------------------------------------
STAFF_SEED = []

# Professionnelles affichées dans l'app cliente (page "Professionnelles")
PROS_CLIENT = []

# ---------------------------------------------------------------------------
# DATES EN FRANÇAIS (sans dépendre de la locale du système : Pyodide n'en a pas)
# ---------------------------------------------------------------------------
MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
             "juil.", "août", "sept.", "oct.", "nov.", "déc."]
MONTHS_FR_LONG = ["janvier", "février", "mars", "avril", "mai", "juin",
                  "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
DAYS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_date(iso: str) -> date:
    try:
        return date.fromisoformat(iso)
    except Exception:
        return date.today()


def format_date_short(iso: str) -> str:
    """'2026-10-08' -> '08 oct.' (format utilisé dans le HTML d'origine)."""
    d = parse_date(iso)
    return f"{d.day:02d} {MONTHS_FR[d.month - 1]}"


def format_date_long(iso: str) -> str:
    """'2026-10-08' -> 'Jeu 08 octobre'."""
    d = parse_date(iso)
    return f"{DAYS_FR[d.weekday()]} {d.day:02d} {MONTHS_FR_LONG[d.month - 1]}"


def digits(phone: str) -> str:
    """Ne garde que les chiffres : sert de clé de recherche ('+228 90 12' -> '2289012')."""
    return "".join(c for c in (phone or "") if c.isdigit())


def new_booking_id() -> str:
    """Identifiant lisible type 'F-483920' (basé sur l'heure → quasi sans collision)."""
    return "F-" + str(int(time.time()))[-6:]


# ---------------------------------------------------------------------------
# RÉSERVATION
# ---------------------------------------------------------------------------
@dataclass
class Booking:
    id: str
    name: str
    phone: str
    service: str
    date: str = ""             # ISO : AAAA-MM-JJ (le HTML stockait "08 oct." en dur)
    time: str = ""
    address: str = ""
    notes: str = ""
    status: str = "new"
    pro: str = DEFAULT_PRO
    phone_key: str = ""        # chiffres seuls -> permet à la cliente de retrouver ses RDV
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.phone_key:
            self.phone_key = digits(self.phone)
        if not self.created_at:
            self.created_at = now_iso()

    def to_dict(self) -> dict:
        """Dictionnaire envoyé à Firebase (l'id sert de clé, on ne le duplique pas)."""
        d = asdict(self)
        d.pop("id")
        return d

    @classmethod
    def from_dict(cls, bid: str, data: dict) -> "Booking":
        """Construit une Booking depuis Firebase en tolérant les champs manquants."""
        data = data if isinstance(data, dict) else {}
        status = data.get("status", "new")
        return cls(
            id=bid,
            name=data.get("name", "Cliente"),
            phone=data.get("phone", ""),
            service=data.get("service", ""),
            date=data.get("date", today_iso()),
            time=data.get("time", ""),
            address=data.get("address", ""),
            notes=data.get("notes", ""),
            status=status if status in STATUS_LABELS else "new",
            pro=data.get("pro", DEFAULT_PRO),
            phone_key=data.get("phone_key", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def demo_bookings() -> list:
    """Les 8 réservations de démonstration du HTML, avec des dates RELATIVES à aujourd'hui."""
    t0 = date.today()
    d0, d1 = t0.isoformat(), (t0 - timedelta(days=1)).isoformat()
    rows = [
        ("F-1028", "Afi Mensah", "+228 90 12 45 67", "Pose de perruque", d0, "14:00", "Agoè — Lomé", "new", "La cliente souhaite être appelée pour préciser le modèle.", DEFAULT_PRO),
        ("F-1027", "Nelly A.", "+228 91 44 28 19", "Tresses", d0, "10:30", "Tokoin — Lomé", "wait", "Tresses à définir avec la cliente.", DEFAULT_PRO),
        ("F-1026", "Ama Kossi", "+228 98 22 10 31", "Tissage", d0, "16:00", "Bè — Lomé", "confirm", "Rappel effectué. Tarif à confirmer après échange.", "Mawussi"),
        ("F-1025", "Mélissa T.", "+228 92 31 08 44", "Manucure", d0, "11:00", "Hédzranawoé — Lomé", "assigned", "Pose simple.", "Akossiwa"),
        ("F-1024", "Dédé A.", "+228 97 05 64 12", "Soin du visage", d0, "09:00", "Cacavéli — Lomé", "progress", "Soin visage demandé.", "Eyram"),
        ("F-1023", "Sika K.", "+228 99 18 72 03", "Pédicure", d1, "15:00", "Adidogomé — Lomé", "done", "Prestation terminée.", "Akossiwa"),
        ("F-1022", "Esther D.", "+228 90 73 16 55", "Maquillage", d1, "18:00", "Nyékonakpoè — Lomé", "confirm", "Maquillage soirée.", "Mawussi"),
        ("F-1021", "Abla Y.", "+228 96 48 33 20", "Massage", d1, "13:30", "Kégué — Lomé", "cancel", "Annulée par la cliente.", "—"),
    ]
    out = []
    for i, (bid, name, phone, svc, d, tm, addr, st, notes, pro) in enumerate(rows):
        out.append(Booking(id=bid, name=name, phone=phone, service=svc, date=d, time=tm,
                           address=addr, notes=notes, status=st, pro=pro,
                           created_at=(datetime.now() - timedelta(minutes=10 * i)).isoformat(timespec="seconds")))
    return out
