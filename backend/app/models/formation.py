#!/usr/bin/env python3
"""
models/formation.py — Catalogue de formations (synthétique, à la place du LMS).

RÔLE
    Pas d'accès au LMS réel : on tient un catalogue de formations SYNTHÉTIQUES
    (recherchées/générées par métier) pour démontrer la recommandation. Chaque
    formation vise une compétence (`skill_cible`) et relève d'un domaine, ce qui
    permet de la proposer en réponse à un écart de compétence détecté au matching.
    Le SUIVI d'avancement d'un collaborateur (statut/progression) est laissé au
    front pour l'instant (les LMS le gèrent en interne — cf. cadrage).

ÉTIQUETAGE
    `synthetique=True` par défaut : contenu fabriqué, jamais présenté comme réel.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Formation(Base):
    __tablename__ = "formations"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str | None] = mapped_column(String(120), default=None)  # organisme / source
    duree: Mapped[str | None] = mapped_column(String(48), default=None)  # ex. "12 h", "3 jours"
    niveau: Mapped[str | None] = mapped_column(
        String(48), default=None
    )  # Débutant / Intermédiaire / Avancé
    domaine: Mapped[str | None] = mapped_column(
        String(64), default=None, index=True
    )  # thème / famille
    tags: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # mots-clés (séparés par des virgules)
    skill_cible: Mapped[str | None] = mapped_column(
        String(200), default=None, index=True
    )  # compétence visée
    synthetique: Mapped[bool] = mapped_column(Boolean, default=True)  # ⚠️ catalogue fabriqué
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
