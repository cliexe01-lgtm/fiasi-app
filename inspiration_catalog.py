"""
Catalogue visuel FIASI.

- 50 modèles locaux par catégorie.
- Les images locales sont embarquées dans l'application : elles restent visibles hors ligne.
- Les recherches complémentaires restent disponibles en ligne.
- Les fichiers locaux servent aussi de référence à l'essayage IA.
"""
from __future__ import annotations

from pathlib import Path
import urllib.parse

BASE = Path(__file__).resolve().parents[1] / "assets" / "catalog"

DATA = {
    "Coiffure & tresses": [
        "Box braids","Cornrows","Knotless braids","Goddess braids","Fulani braids",
        "Stitch braids","Passion twists","Senegalese twists","Lemonade braids","Ghana braids",
        "Micro braids","Jumbo braids","Boho braids","Butterfly locs","Faux locs",
        "Marley twists","Mini twists","Tresses perlées","Tresses avec motifs","Tresses en chignon",
        "Tresses côté","Tresses queue-de-cheval","Feed-in braids","Triangle braids","Tribal braids",
        "Invisible braids","Braids mariage","Braids ombré","Braids miel","Braids bordeaux",
        "Braids blondes","Braids rouges","Cornrows zigzag","Cornrows simples","Cornrows créatives",
        "Tresses courtes","Tresses longues","Tresses moyennes","Tresses fines","Tresses épaisses",
        "Twists courtes","Twists longues","Locs retwist","Microlocs","Starter locs",
        "Natural afro","Wash & go","Chignon tressé","Queue haute tressée","Demi-tête tressée",
    ],
    "Perruques": [
        "Afro wig","Bob asymétrique","Bob bouclé","Bob droit","Body wave","Closure 4x4",
        "Closure 5x5","Closure 6x6","Deep wave","Frontal 13x4","Frontal 13x6","Glueless wig",
        "HD lace","Jerry curl","Kinky curly","Kinky straight","Lace droite","Lace ondulée",
        "Lace pixie","Longue bouclée","Longue ondulée","Longue raide","Mi-longue","Pixie cut",
        "Perruque bordeaux","Perruque brune","Perruque blonde","Perruque courte",
        "Perruque effet naturel","Perruque miel","Perruque noire","Perruque ombré","Perruque rouge",
        "Perruque raie côté","Perruque raie milieu","Perruque XXL","Queue haute","Silky straight",
        "Water wave","Loose wave","Body wave naturelle","Curly bob","Deep curl","Wig avec baby hair",
        "Wig naturelle","Wig sans colle","Wig événement","Wig mariage","Wig soirée","Wig volume",
    ],
    "Onglerie": [
        "Baby boomer","Cat eye","Chrome argent","Chrome doré","Chrome rose","Effet miroir",
        "French classique","French colorée","Glitter argent","Glitter doré","Manucure classique",
        "Manucure express","Manucure gel","Manucure naturelle","Nail art africain","Nail art floral",
        "Nail art géométrique","Nail art mariage","Nude","Ombre nails","Ongles amande",
        "Ongles coffin","Ongles courts","Ongles longs","Ongles moyens","Ongles stiletto",
        "Pédicure classique","Pédicure express","Pédicure gel","Pédicure spa","Perles","Paillettes",
        "Strass","Rouge glamour","Bordeaux","Rose poudré","Rose vif","Blanc élégant","Noir brillant",
        "Noir mat","Vert émeraude","Bleu ciel","Bleu royal","Violet","Orange","Jaune soleil",
        "Terracotta","Nude caramel","Marble nails","Aura nails",
    ],
    "Maquillage": [
        "Bronze glam","Contour naturel","Contour sculpté","Cut crease","Douceur rosée","Fox eyes",
        "Full glam","Golden glam","Halo eyes","Liner coloré","Liner graphique","Look Ankara",
        "Look chocolat","Look doré","Look Kente","Maquillage africain","Maquillage anniversaire",
        "Maquillage artistique","Maquillage cocktail","Maquillage discret","Maquillage événementiel",
        "Maquillage fête","Maquillage jour","Maquillage mariage","Maquillage mariée glam",
        "Maquillage naturel","Maquillage nude","Maquillage peau noire","Maquillage peau métissée",
        "Maquillage photo","Maquillage professionnel","Maquillage scène","Maquillage soirée",
        "Maquillage sophistiqué","Maquillage shooting","Peau glowy","Peau matte","Red lips",
        "Smoky brun","Smoky eyes","Smoky noir","Soft glam","Gloss nude","Blush lumineux",
        "Bordeaux lips","Maquillage traditionnel","Monochrome","Éditorial","Look soirée","Look naturel",
    ],
}

PREFIX = {"Coiffure & tresses":"hair","Perruques":"wig","Onglerie":"nail","Maquillage":"makeup"}
TRYON_CATEGORIES = {"Coiffure & tresses", "Perruques"}

def build_items(category: str):
    prefix = PREFIX[category]
    items = []
    for i, name in enumerate(DATA[category], 1):
        local_rel = f"catalog/{prefix}_{i:02d}.png"
        local_abs = BASE / f"{prefix}_{i:02d}.png"
        items.append({
            "id": f"{prefix}-{i}",
            "name": name,
            "image": local_rel,
            "reference": str(local_abs),
        })
    return items

CATALOG = {category: build_items(category) for category in DATA}

def online_search_url(category: str) -> str:
    query = {
        "Coiffure & tresses": "coiffures tresses africaines femmes",
        "Perruques": "perruques lace wig coiffure africaine",
        "Onglerie": "manucure pédicure nail art africain",
        "Maquillage": "maquillage femme noire beauté",
    }.get(category, "FIASI beauté")
    return "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(query)
