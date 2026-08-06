#!/usr/bin/env python3
"""
models/evaluation_bilan.py — Bilan d'évaluation soumis par le manager/RH (historique).

RÔLE
    Trace une APPRÉCIATION GLOBALE portée sur un collaborateur au fil de l'eau :
    note d'ensemble (étoiles 1-5), commentaire libre, date, évaluateur. À la
    différence de `CompetenceEvaluation` (une note COURANTE par compétence, upsert),
    ce bilan est un JOURNAL : chaque soumission crée une nouvelle ligne, alimentant
    l'« Historique des évaluations » de la fiche collaborateur.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EvaluationBilan(Base):
    __tablename__ = "evaluation_bilans"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    evaluateur_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None)
    type: Mapped[str] = mapped_column(String(16), default="mission")  # mission | performance
    note: Mapped[int | None] = mapped_column(Integer, default=None)   # appréciation globale 1-5
    commentaire: Mapped[str | None] = mapped_column(Text, default=None)
    competences_detectees: Mapped[int] = mapped_column(Integer, default=0)  # trace extraction
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
