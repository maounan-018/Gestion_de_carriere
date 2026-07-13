#!/usr/bin/env python3
"""
models/skill_crosswalk.py — Alignement inter-référentiels (O*NET/SFIA → pivot ESCO).

RÔLE
    Relie une compétence issue d'O*NET ou de SFIA à sa compétence ÉQUIVALENTE
    dans ESCO (le pivot canonique). C'est la table qui dédoublonne le graphe :
    « financial analysis » (O*NET) ↔ « analyse financière » (ESCO) deviennent
    reliés. Non destructif : les deux nœuds Skill subsistent (les liens
    occupation↔compétence restent valides), on ajoute juste la correspondance.

    Chaque alignement porte sa confiance et sa méthode (embedding→reranker→LLM),
    pour l'auditabilité et une éventuelle relecture RH.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SkillCrosswalk(Base):
    __tablename__ = "skill_crosswalks"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)     # O*NET / SFIA
    canonical_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)  # ESCO (pivot)
    source: Mapped[str] = mapped_column(String(16), index=True)   # ONET | SFIA
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1 (reranker × LLM)
    method: Mapped[str] = mapped_column(String(12), default="llm")
    validated: Mapped[bool] = mapped_column(Boolean, default=False)  # relu par un humain ?

    __table_args__ = (
        # une compétence source pointe vers au plus UNE compétence canonique
        Index("ix_crosswalk_source_unique", "source_skill_id", unique=True),
    )
