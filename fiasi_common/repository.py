"""
repository.py — Couche "métier" au-dessus de Firebase.

Les écrans ne parlent JAMAIS directement à Firebase : ils appellent ces fonctions.
Ainsi, si vous changez de base de données (Firestore, Supabase…), seul ce fichier
et firebase_client.py changent.

STRUCTURE DE LA BASE (voir aussi firebase/structure_exemple.json) :

    /bookings/{id}      une réservation   (écrite par la CLIENTE, modifiée par la RÉCEPTION)
    /staff/{prénom}     une professionnelle (gérée par la RÉCEPTION)
    /activities/{push}  journal d'activité  (écrit par les DEUX apps)

FLUX D'INTERACTION ENTRE LES DEUX APPS :
    CLIENTE   --create_booking-->  /bookings/F-xxxx   (status = "new")
    RÉCEPTION <--list_bookings---  (polling toutes les POLL_SECONDS secondes)
    RÉCEPTION --update_booking-->  status = "confirm" / pro = "Mawussi" …
    CLIENTE   <--list_bookings_for_phone--  voit le nouveau statut, reçoit une notification
"""
from __future__ import annotations

from .models import (Booking, digits, now_iso)


class Repository:
    def __init__(self, store):
        self.store = store

    # Texte affiché dans l'interface : "Firebase" ou "Démo locale"
    @property
    def mode_label(self) -> str:
        return self.store.label

    # ------------------------------------------------------------------ RÉSERVATIONS
    async def list_bookings(self) -> list:
        """TOUTES les réservations (utilisé par la réception), les plus récentes d'abord."""
        raw = await self.store.get("bookings") or {}
        items = [Booking.from_dict(k, v) for k, v in raw.items()] if isinstance(raw, dict) else []
        items.sort(key=lambda b: b.created_at, reverse=True)
        return items

    async def list_bookings_for_phone(self, phone: str) -> list:
        """
        Réservations d'UN numéro (utilisé par la cliente).
        On interroge Firebase avec orderBy=phone_key&equalTo=… pour ne télécharger
        que ses propres réservations (nécessite `.indexOn: ["phone_key"]`).
        """
        key = digits(phone)
        if not key:
            return []
        raw = await self.store.get("bookings", order_by="phone_key", equal_to=key) or {}
        items = [Booking.from_dict(k, v) for k, v in raw.items()] if isinstance(raw, dict) else []
        items.sort(key=lambda b: b.created_at, reverse=True)
        return items

    async def create_booking(self, booking: Booking) -> None:
        """La cliente crée sa réservation (PUT = on choisit l'id nous-mêmes)."""
        await self.store.put(f"bookings/{booking.id}", booking.to_dict())

    async def update_booking(self, booking_id: str, changes: dict) -> None:
        """La réception modifie statut / professionnelle (PATCH = champs ciblés)."""
        changes = dict(changes)
        changes["updated_at"] = now_iso()
        await self.store.patch(f"bookings/{booking_id}", changes)

    # ------------------------------------------------------------------ ACTIVITÉ
    async def add_activity(self, text: str) -> None:
        """Ajoute une ligne au journal (affiché dans « Activité récente »)."""
        await self.store.post("activities", {"text": text, "ts": now_iso()})

    async def list_activities(self, limit: int = 8) -> list:
        """Dernières activités, la plus récente en premier : liste de dicts {text, ts}."""
        raw = await self.store.get("activities", order_by="$key", limit_last=limit) or {}
        rows = [v for v in raw.values() if isinstance(v, dict)] if isinstance(raw, dict) else []
        rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
        return rows[:limit]

    # ------------------------------------------------------------------ ÉQUIPE
    async def list_staff(self) -> list:
        raw = await self.store.get("staff") or {}
        if not isinstance(raw, dict):
            return []
        rows = [dict(v, name=k) for k, v in raw.items() if isinstance(v, dict)]
        rows.sort(key=lambda r: (r.get("name") or "").lower())
        return rows

    async def update_staff(self, name: str, changes: dict) -> None:
        await self.store.patch(f"staff/{name}", changes)
