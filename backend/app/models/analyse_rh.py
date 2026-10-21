#!/usr/bin/env python3
"""
models/analyse_rh.py — Analyse stratégique RH (HRBP) PERSISTÉE.

RÔLE
    Stocke la dernière synthèse IA des indicateurs consolidés comme SOURCE
    DURABLE. Le tableau de bord HRBP présente ainsi l'analyse COURANTE sans que
    la HRBP ait à « lancer » un calcul à chaque visite : elle voit la dernière
    synthèse persistée, avec sa date, et n'actualise (recalcul IA) que lorsque
    la donnée a évolué — un rappel hebdomadaire l'y invite au bon moment.
    Une seule ligne « courante » par périmètre (`scope`, défaut « global ») :
    recalculer met à jour la même ligne (jamais de perte).

EMPLACEMENT MVC
    Couche "models" : table + colonnes.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AnalyseRh(Base):
    __tablename__ = "analyses_rh"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(64), unique=True, index=True, default="global")
    synthese: Mapped[str] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(120), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
