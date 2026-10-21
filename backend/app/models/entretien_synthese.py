#!/usr/bin/env python3
"""
models/entretien_synthese.py — Synthèse de préparation d'entretien (sortie IA persistée).

RÔLE
    Conserve la SYNTHÈSE produite au fil de la simulation de préparation d'entretien
    annuel (co-pilote IA), par profil. Source durable : la simulation « produit » un
    livrable réutilisable (relu plus tard, exporté en PDF, présenté à l'entretien).
    Une seule ligne courante par profil (upsert), comme les autres sorties IA
    persistées (recommandations, analyse RH).

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EntretienSynthese(Base):
    __tablename__ = "entretien_syntheses"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(
        ForeignKey("profils.id"), index=True, unique=True
    )  # une synthèse courante par profil
    synthese: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
