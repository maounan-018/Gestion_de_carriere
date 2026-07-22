#!/usr/bin/env python3
"""
models/candidature.py — Candidature d'un profil à une offre (→ score d'évaluation).

RÔLE
    Relie un `Profil` (candidat) à une `Offre`. Le matching confronte les
    compétences DÉTENUES (ProfilCompetence) aux ATTENDUS de l'offre
    (OffreCompetence) → `score` d'évaluation + snapshot des écarts (traçabilité).

    ⚠️ RÈGLE MÉTIER : le score est indicatif, PAS un filtre. Un candidat < 100 %
    peut être RETENU — la décision reste humaine (statut + decided_by).

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CandidatureStatut:
    DEPOSEE = "deposee"
    EN_EVALUATION = "en_evaluation"
    RETENUE = "retenue"        # sélectionnée (même si score < 100 %)
    REJETEE = "rejetee"
    RETIREE = "retiree"        # retirée par le candidat


class Candidature(Base):
    __tablename__ = "candidatures"

    id: Mapped[int] = mapped_column(primary_key=True)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offres.id"), index=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    statut: Mapped[str] = mapped_column(String(16), default=CandidatureStatut.DEPOSEE, index=True)
    score: Mapped[float | None] = mapped_column(Float, default=None)        # score d'évaluation (0-100)
    evaluation_json: Mapped[str | None] = mapped_column(Text, default=None)  # snapshot couvertes/écarts (traçabilité)
    motivation: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
    reevaluated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)  # dernière réévaluation (traçabilité)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)  # décideur (humain)

    __table_args__ = (
        # un profil ne candidate qu'une fois par offre
        Index("ix_candidature_unique", "offre_id", "profil_id", unique=True),
    )
