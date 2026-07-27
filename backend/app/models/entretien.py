#!/usr/bin/env python3
"""
models/entretien.py — Entretien de carrière (annuel manager ↔ collab, ou RH ↔ collab).

RÔLE
    Suit les entretiens à mener / menés, pour la « veille » RH (combien réalisés,
    planifiés, en retard) et pour alimenter des alertes (entretiens en retard). Deux
    types : `annuel` (mené par le manager) et `rh` (mené par la RH). Distinct du
    contenu d'évaluation (non modélisé ici) : on suit ici la TENUE de l'entretien.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EntretienType:
    ANNUEL = "annuel"   # entretien annuel, mené par le manager
    RH = "rh"           # entretien de carrière, mené par la RH


class EntretienStatut:
    PLANIFIE = "planifie"
    REALISE = "realise"
    EN_RETARD = "en_retard"


class Entretien(Base):
    __tablename__ = "entretiens"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)  # collaborateur concerné
    type: Mapped[str] = mapped_column(String(12), default=EntretienType.ANNUEL, index=True)
    statut: Mapped[str] = mapped_column(String(12), default=EntretienStatut.PLANIFIE, index=True)
    date_prevue: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    date_realisee: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    conduit_par: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)  # manager / RH
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
