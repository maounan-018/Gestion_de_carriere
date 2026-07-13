#!/usr/bin/env python3
"""
models/occupation.py — Métier/rôle (ESCO occupation, O*NET-SOC) + lien métier↔compétence.

RÔLE
    `Occupation` = un métier/poste type du référentiel. `OccupationSkill` relie un
    métier aux compétences qu'il requiert (essentielles ou optionnelles) — c'est ce
    lien qui permet, plus tard, « quel poste pour ce profil » et « quelles
    compétences me manquent pour ce poste ».

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from sqlalchemy import String, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SkillRequirement:
    ESSENTIAL = "essential"   # compétence indispensable au métier
    OPTIONAL = "optional"     # compétence utile mais non requise


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[int] = mapped_column(primary_key=True)
    label_fr: Mapped[str] = mapped_column(String(300), index=True)
    label_en: Mapped[str] = mapped_column(String(300), index=True)
    description_fr: Mapped[str | None] = mapped_column(Text, default=None)
    description_en: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[str] = mapped_column(String(16), index=True)        # ESCO | ONET
    source_uri: Mapped[str | None] = mapped_column(String(400), default=None)
    code: Mapped[str | None] = mapped_column(String(40), default=None)  # ISCO (ESCO) / SOC (O*NET)


class OccupationSkill(Base):
    __tablename__ = "occupation_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    occupation_id: Mapped[int] = mapped_column(ForeignKey("occupations.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    requirement: Mapped[str] = mapped_column(String(12), default=SkillRequirement.ESSENTIAL)

    __table_args__ = (
        Index("ix_occupation_skill_unique", "occupation_id", "skill_id", unique=True),
    )
