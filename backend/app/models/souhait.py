#!/usr/bin/env python3
"""
models/souhait.py — Souhait d'évolution d'un collaborateur.

RÔLE
    Aspiration exprimée par un collaborateur (poste visé, mobilité, mission) qu'il
    peut garder en brouillon puis POUSSER à son manager (`pushed`). Le manager
    consulte les souhaits poussés par son équipe (`/api/souhaits/recus`) pour
    préparer les entretiens et alimenter la RH. Distinct des `aspirations` (texte
    libre du profil) : ici chaque souhait est une entité suivie avec un statut.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SouhaitKind:
    CARRIERE = "carriere"  # évolution de carrière / poste visé
    MISSION = "mission"  # mission / gig ponctuel


class SouhaitStatut:
    BROUILLON = "brouillon"  # visible du seul collaborateur
    POUSSE = "pousse"  # poussé au manager
    EN_DISCUSSION = "en_discussion"  # en cours d'échange manager/RH
    ACCORDE = "accorde"
    REFUSE = "refuse"


class Souhait(Base):
    __tablename__ = "souhaits"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    titre: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(12), default=SouhaitKind.CARRIERE)
    horizon: Mapped[str | None] = mapped_column(String(32), default=None)  # ex. "6 mois", "1-2 ans"
    description: Mapped[str | None] = mapped_column(Text, default=None)
    statut: Mapped[str] = mapped_column(String(16), default=SouhaitStatut.BROUILLON, index=True)
    pushed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # poussé au manager
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
