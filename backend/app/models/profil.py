#!/usr/bin/env python3
"""
models/profil.py — Profil collaborateur + compétences DÉTENUES.

RÔLE
    `Profil` = profil de carrière d'un collaborateur (distinct du compte User =
    identité/auth ; lié à lui, ou synthétique pour la démo). `ProfilCompetence` =
    les compétences que la personne POSSÈDE, avec leur NIVEAU de maîtrise et la
    SOURCE de détection (CV, évaluation de mission, évaluation de performance,
    déclaratif, mini-jeu). C'est ce capital de compétences qui est confronté aux
    attendus d'une offre (candidature -> score) et qui alimente les recommandations.

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CompetenceSource:
    """D'où provient une compétence détenue (traçabilité de la cartographie)."""

    CV = "cv"
    EVAL_MISSION = "evaluation_mission"  # évaluation de mission par le manager
    EVAL_PERF = "evaluation_performance"
    DECLARATIF = "declaratif"  # déclaré par le collaborateur
    JEU = "jeu"  # mini-jeu (futur)
    FICHE = "fiche"  # déduit du poste occupé


class Profil(Base):
    __tablename__ = "profils"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None, index=True
    )  # null = persona synthétique
    nom: Mapped[str] = mapped_column(String(120))
    prenom: Mapped[str | None] = mapped_column(String(120), default=None)
    matricule: Mapped[str | None] = mapped_column(
        String(64), default=None, index=True
    )  # 64 : matricules synthétiques DEMO-CARTO (jusqu'à 38 car.)
    poste_actuel: Mapped[str | None] = mapped_column(String(200), default=None)
    departement_key: Mapped[str | None] = mapped_column(String(48), default=None, index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    date_entree: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    aspirations: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # souhaits d'évolution (pour la reco)
    # Profil de carrière AUTO-DÉCLARÉ (édité par le collaborateur/manager/RH lui-même) —
    # enrichit la reco et la préparation d'entretiens. Tous nullables.
    bio: Mapped[str | None] = mapped_column(Text, default=None)  # description / « à propos »
    poste_vise: Mapped[str | None] = mapped_column(String(200), default=None)  # poste ciblé
    horizon: Mapped[str | None] = mapped_column(String(32), default=None)  # ex : « 1 an »
    type_evolution: Mapped[str | None] = mapped_column(
        String(48), default=None
    )  # management / expertise / mobilité géo / mission transverse
    mobilite_geo: Mapped[str | None] = mapped_column(
        String(200), default=None
    )  # zones géographiques
    disponibilite: Mapped[str | None] = mapped_column(
        String(64), default=None
    )  # ex : « 6 à 12 mois »
    # CV du collaborateur (fichier PDF conservé côté serveur, data/cv_profil/{id}.pdf).
    # Source durable : alimente extractions/analyses et est présenté au manager / à la HRBP.
    cv_filename: Mapped[str | None] = mapped_column(String(255), default=None)  # nom d'origine
    cv_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    synthetique: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class ProfilCompetence(Base):
    __tablename__ = "profil_competences"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    libelle: Mapped[str] = mapped_column(String(300))
    categorie: Mapped[str | None] = mapped_column(String(24), default=None)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"), default=None, index=True)
    skill_label_fr: Mapped[str | None] = mapped_column(String(300), default=None)
    niveau: Mapped[int | None] = mapped_column(Integer, default=None)  # 1-5 / niveau SFIA
    source: Mapped[str] = mapped_column(String(24), default=CompetenceSource.DECLARATIF)
    rerank_score: Mapped[float | None] = mapped_column(Float, default=None)
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    __table_args__ = (Index("ix_profil_comp_profil", "profil_id"),)
