#!/usr/bin/env python3
"""
models/skill_mapping.py — Crosswalk : lien compétence unifiée ↔ entrée d'un référentiel.

RÔLE
    Chaque `Skill` interne peut correspondre à une entrée d'ESCO, d'O*NET et/ou de
    SFIA. `SkillMapping` enregistre CHAQUE correspondance avec sa provenance
    (source, identifiant externe), son score de confiance et la MÉTHODE d'alignement
    (exact/embedding/reranker/llm/manuel) + un drapeau de validation humaine.
    C'est la table qui rend le référentiel unifié auditable et réexploitable.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MappingMethod:
    EXACT = "exact"         # correspondance exacte de libellé/identifiant
    EMBEDDING = "embedding"  # rapprochement vectoriel (bge-m3)
    RERANKER = "reranker"    # confirmé par le reranker (bge-reranker-v2-m3)
    LLM = "llm"             # validé par un LLM (lc-normaliseur)
    MANUAL = "manual"        # validé/saisi par un humain (RH)


class SkillMapping(Base):
    __tablename__ = "skill_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    source: Mapped[str] = mapped_column(String(16), index=True)          # ESCO | ONET | SFIA
    external_id: Mapped[str] = mapped_column(String(400), index=True)     # URI ESCO / id O*NET / code SFIA
    external_label: Mapped[str | None] = mapped_column(String(300), default=None)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)         # 0..1
    method: Mapped[str] = mapped_column(String(12), default=MappingMethod.EXACT)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)       # relu par un humain ?

    __table_args__ = (
        Index("ix_skill_mapping_unique", "skill_id", "source", "external_id", unique=True),
    )
