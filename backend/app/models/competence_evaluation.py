#!/usr/bin/env python3
"""
models/competence_evaluation.py — Évaluation d'une compétence détenue (score persisté).

RÔLE
    Porte le SCORE d'acquisition d'une compétence, par SOURCE d'évaluation :
      - `manager`  : évaluation du manager (1 à 10) — poids prépondérant ;
      - `peer`     : avis des pairs (surtout savoir-être) — futur ;
      - `jeu`      : mini-jeux d'évaluation — futur.
    Une ligne COURANTE par (compétence, source) : une nouvelle évaluation REMPLACE
    la précédente (upsert). Le % d'acquisition d'une compétence combine ces sources
    (cf. evaluation_service), l'évaluation du manager pesant le plus.

    Distinct de `ProfilCompetence.niveau` (niveau déclaratif/pré-chargé) : une
    compétence seulement déclarée (CV/fiche) SANS évaluation reste « en attente ».

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EvaluationSource:
    MANAGER = "manager"   # évaluation du manager (poids fort)
    PEER = "peer"         # avis des pairs (savoir-être) — futur
    JEU = "jeu"           # mini-jeux d'évaluation — futur


class CompetenceEvaluation(Base):
    __tablename__ = "competence_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_competence_id: Mapped[int] = mapped_column(
        ForeignKey("profil_competences.id"), index=True)
    source: Mapped[str] = mapped_column(String(12), default=EvaluationSource.MANAGER)
    score: Mapped[int] = mapped_column(Integer)                     # 1 à 10
    evaluateur_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    # Contexte d'évaluation de MISSION : l'offre au titre de laquelle le manager a
    # évalué la compétence (attribution « évaluée par X dans le cadre de la mission Y »).
    offre_id: Mapped[int | None] = mapped_column(ForeignKey("offres.id"), default=None, index=True)
    commentaire: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("profil_competence_id", "source", name="uq_comp_eval_source"),
    )
