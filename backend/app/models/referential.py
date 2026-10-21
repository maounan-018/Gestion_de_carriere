#!/usr/bin/env python3
"""
models/referential.py — Sources de référentiels (ESCO / O*NET / SFIA).

RÔLE
    Trace chaque référentiel importé : code, version, langues, licence et
    volumétrie. Sert de journal d'ingestion et de provenance pour le graphe.

EMPLACEMENT MVC
    Couche "models" : entité ORM (aucune logique métier ici).
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SourceCode:
    """Codes des référentiels supportés (bilingues FR/EN, tous gratuits)."""

    ESCO = "ESCO"  # Union européenne — pivot multilingue
    ONET = "ONET"  # États-Unis — richesse métier (traduit FR localement)
    SFIA = "SFIA"  # IT/digital — niveaux de responsabilité 1..7


class ReferentialSource(Base):
    __tablename__ = "referential_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)  # ESCO/ONET/SFIA
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str | None] = mapped_column(String(40), default=None)
    languages: Mapped[str | None] = mapped_column(String(80), default=None)  # ex. "fr,en"
    license: Mapped[str | None] = mapped_column(String(80), default=None)
    # Mention d'attribution EXIGÉE par le fournisseur, à afficher sur la plateforme.
    attribution: Mapped[str | None] = mapped_column(String(400), default=None)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    n_skills: Mapped[int] = mapped_column(Integer, default=0)
    n_occupations: Mapped[int] = mapped_column(Integer, default=0)
