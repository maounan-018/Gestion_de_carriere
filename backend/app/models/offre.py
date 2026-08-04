#!/usr/bin/env python3
"""
models/offre.py — Offre / Mission / Projet / Gig (DÉRIVE d'une Fiche de poste).

RÔLE
    Une `Offre` est une opportunité à pourvoir, POUSSÉE par la RH (offre de poste)
    ou un manager (mission/projet/gig). Ses attendus sont **basés sur une Fiche de
    poste de référence** mais **modifiables AU NIVEAU DE L'OFFRE** — la Fiche de
    référence, elle, n'est JAMAIS modifiée. `OffreCompetence` porte ces attendus
    overridables (avec importance essentielle/souhaitée et niveau requis), copiés
    de la Fiche à la création puis éditables.

    C'est contre ces `OffreCompetence` qu'une candidature est évaluée (score).

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, Boolean, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OffreType:
    OFFRE_POSTE = "offre_poste"   # RH : poste à pourvoir
    MISSION = "mission"          # manager : mission
    PROJET = "projet"            # manager : projet
    GIG = "gig"                  # manager : gig court


class OffreStatut:
    BROUILLON = "brouillon"
    OUVERTE = "ouverte"
    POURVUE = "pourvue"
    FERMEE = "fermee"
    ANNULEE = "annulee"


class Offre(Base):
    __tablename__ = "offres"

    id: Mapped[int] = mapped_column(primary_key=True)
    fiche_id: Mapped[int | None] = mapped_column(ForeignKey("fiches.id"), default=None, index=True)  # référence dérivée
    type: Mapped[str] = mapped_column(String(16), default=OffreType.OFFRE_POSTE, index=True)
    titre: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    localisation: Mapped[str | None] = mapped_column(String(120), default=None)  # ville / site
    duree: Mapped[str | None] = mapped_column(String(64), default=None)          # ex : « 6 mois » (mission/projet)
    perimetre_bmci: Mapped[str | None] = mapped_column(String(160), default=None)
    departement_key: Mapped[str | None] = mapped_column(String(48), default=None, index=True)
    statut: Mapped[str] = mapped_column(String(12), default=OffreStatut.BROUILLON, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)  # qui pousse
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)  # manager concerné (notif)
    date_ouverture: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    synthetique: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))


class OffreCompetence(Base):
    """Attendu de l'offre (OVERRIDABLE) — copié de la Fiche puis éditable au niveau offre."""
    __tablename__ = "offre_competences"

    id: Mapped[int] = mapped_column(primary_key=True)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offres.id"), index=True)
    libelle: Mapped[str] = mapped_column(String(300))
    categorie: Mapped[str | None] = mapped_column(String(24), default=None)  # metier/comportementale/...
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"), default=None, index=True)
    skill_label_fr: Mapped[str | None] = mapped_column(String(300), default=None)
    importance: Mapped[str] = mapped_column(String(12), default="essentielle")  # essentielle | souhaitee
    niveau_requis: Mapped[int | None] = mapped_column(Integer, default=None)     # 1-5 / niveau SFIA
    rerank_score: Mapped[float | None] = mapped_column(Float, default=None)
    source: Mapped[str] = mapped_column(String(12), default="fiche")             # fiche | ajout_offre

    __table_args__ = (Index("ix_offre_comp_offre", "offre_id"),)
