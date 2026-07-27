#!/usr/bin/env python3
"""
models/carriere.py — Enrichissements « carrière » d'un profil.

RÔLE
    Éléments du parcours affichés sur la fiche profil, au-delà des compétences :
      - `ProfilStation` : jalons de la trajectoire (passés, actuel, objectif) —
        alimente la « courbe » de progression.
      - `PeerReview` : avis des pairs (retour qualitatif + note en étoiles).
    Rattachés à un `Profil`. Synthétiques en démo (via le profil parent).

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class StationEtat:
    PASSE = "passe"       # jalon franchi
    ACTUEL = "actuel"     # position actuelle
    OBJECTIF = "objectif"  # cible visée


class ProfilStation(Base):
    __tablename__ = "profil_stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    periode: Mapped[str] = mapped_column(String(48))          # ex. "2021", "Aujourd'hui", "Objectif"
    titre: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    etat: Mapped[str] = mapped_column(String(12), default=StationEtat.PASSE)
    ordre: Mapped[int] = mapped_column(Integer, default=0)    # ordre d'affichage


class PeerReview(Base):
    __tablename__ = "peer_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    auteur_nom: Mapped[str] = mapped_column(String(120))
    auteur_role: Mapped[str | None] = mapped_column(String(120), default=None)
    initiales: Mapped[str | None] = mapped_column(String(8), default=None)
    texte: Mapped[str] = mapped_column(Text)
    etoiles: Mapped[int] = mapped_column(Integer, default=5)  # 1-5
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
