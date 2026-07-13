#!/usr/bin/env python3
"""
models/skill.py — Compétence unifiée (nœud du graphe) + relations compétence↔compétence.

RÔLE
    `Skill` = identifiant interne UNIQUE d'une compétence, bilingue FR/EN, quel
    que soit le référentiel d'origine. L'embedding (bge-m3) est stocké à part dans
    la table vectorielle sqlite-vec `vec_skills` (clé = Skill.id), pas ici.
    `SkillRelation` porte la hiérarchie et les liens transversaux (broader/narrower/
    related/leads_to) qui font du référentiel un GRAPHE.

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SkillType:
    KNOWLEDGE = "knowledge"      # savoir (ESCO knowledge)
    SKILL = "skill"             # savoir-faire (ESCO skill/competence)
    TRANSVERSAL = "transversal"  # compétence transversale
    DIGITAL = "digital"         # compétence SFIA (IT/digital)
    OTHER = "other"


class RelationType:
    BROADER = "broader"      # compétence parente (plus générale)
    NARROWER = "narrower"    # compétence enfant (plus spécifique)
    RELATED = "related"      # compétence liée (transversale)
    LEADS_TO = "leads_to"    # progression de carrière (mène à)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)  # = rowid pour vec_skills
    label_fr: Mapped[str] = mapped_column(String(300), index=True)
    label_en: Mapped[str] = mapped_column(String(300), index=True)
    description_fr: Mapped[str | None] = mapped_column(Text, default=None)
    description_en: Mapped[str | None] = mapped_column(Text, default=None)
    skill_type: Mapped[str] = mapped_column(String(20), default=SkillType.OTHER, index=True)
    sfia_level: Mapped[int | None] = mapped_column(Integer, default=None)  # 1..7 si issu de SFIA
    canonical: Mapped[bool] = mapped_column(Boolean, default=True)          # False = doublon fusionné
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))


class SkillRelation(Base):
    __tablename__ = "skill_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(20), default=RelationType.RELATED)

    __table_args__ = (
        Index("ix_skill_relation_unique", "parent_id", "child_id", "relation_type", unique=True),
    )
