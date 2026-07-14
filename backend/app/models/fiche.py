#!/usr/bin/env python3
"""
models/fiche.py — Fiche de poste (RÉFÉRENCE) + ses compétences attendues.

RÔLE
    Démarre le modèle métier : `Fiche` = description de RÉFÉRENCE d'un rôle (stable),
    `FicheCompetence` = les compétences attendues, TYPÉES (métier/comportementale/…)
    et ANCRÉES au graphe (skill_id canonique). C'est cette liste de compétences qui
    servira au matching d'un candidat (score + écarts). Une Offre/Mission dérivera
    plus tard d'une Fiche (attendus overridables au niveau de l'offre, jamais de la fiche).

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, Boolean, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FicheSource:
    GENEREE = "generee"     # produite par génération IA (synthétique)
    IMPORTEE = "importee"   # importée d'un document réel (traitée localement)


class Fiche(Base):
    __tablename__ = "fiches"

    id: Mapped[int] = mapped_column(primary_key=True)
    departement_key: Mapped[str] = mapped_column(String(48), index=True)
    perimetre_bmci: Mapped[str] = mapped_column(String(160))          # département (nom)
    famille_metier: Mapped[str | None] = mapped_column(String(120), default=None)  # pôle
    intitule_poste: Mapped[str] = mapped_column(String(200), index=True)
    code_poste: Mapped[str | None] = mapped_column(String(120), default=None)
    mission: Mapped[str | None] = mapped_column(Text, default=None)
    activites_principales: Mapped[str | None] = mapped_column(Text, default=None)
    langues: Mapped[str | None] = mapped_column(Text, default=None)
    indicateurs_performances: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[str] = mapped_column(String(12), default=FicheSource.GENEREE)
    synthetique: Mapped[bool] = mapped_column(Boolean, default=True)   # ⚠️ contenu généré
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_fiche_dept_intitule", "departement_key", "intitule_poste", unique=True),
    )


class FicheCompetence(Base):
    __tablename__ = "fiche_competences"

    id: Mapped[int] = mapped_column(primary_key=True)
    fiche_id: Mapped[int] = mapped_column(ForeignKey("fiches.id"), index=True)
    libelle: Mapped[str] = mapped_column(String(300))                 # compétence telle qu'écrite
    categorie: Mapped[str | None] = mapped_column(String(24), default=None)  # metier/comportementale/…
    implicite: Mapped[bool] = mapped_column(Boolean, default=False)
    # ancrage graphe (compétence canonique ESCO/O*NET/SFIA)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"), default=None, index=True)
    skill_label_fr: Mapped[str | None] = mapped_column(String(300), default=None)
    rerank_score: Mapped[float | None] = mapped_column(Float, default=None)
