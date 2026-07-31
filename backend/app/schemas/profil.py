#!/usr/bin/env python3
"""
schemas/profil.py — Contrats d'entrée/sortie du Profil collaborateur.

RÔLE
    Forme des données d'un profil (identité, poste, aspirations) et de ses
    compétences détenues (libellé, niveau 1-5, provenance). C'est la base de la
    cartographie individuelle et du matching candidat ↔ offre à venir.

    Le champ `aspirations` porte le « poste visé / souhaits d'évolution » saisi
    par le collaborateur dans la maquette — il oriente les recommandations.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Provenances valides d'une compétence (miroir de models.profil.CompetenceSource).
SOURCES = ("cv", "evaluation_mission", "evaluation_performance", "declaratif", "jeu", "fiche")


class ProfilCompetenceIn(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=300)
    categorie: str | None = Field(None, max_length=24,
                                  description="metier | comportementale | transversale | outil_technologie")
    niveau: int | None = Field(None, ge=1, le=5, description="Niveau de maîtrise 1-5 (aligné SFIA).")
    source: str = Field("declaratif",
                        description="Provenance : " + " | ".join(SOURCES))


class ProfilCompetenceOut(ProfilCompetenceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skill_id: int | None = None
    skill_label_fr: str | None = None


class CvExtractionRequest(BaseModel):
    """Entrée de l'extraction CV → profil : le texte du CV/parcours à analyser."""
    texte: str = Field(..., min_length=10, description="Texte du CV / parcours à analyser.")
    top_k: int = Field(1, ge=1, le=5,
                       description="Compétences canoniques rapprochées par compétence extraite.")
    remplacer: bool = Field(True, description="Remplacer les compétences déjà issues d'un CV "
                                              "(source=cv) avant d'ajouter les nouvelles.")


class EvaluationExtractionRequest(BaseModel):
    """Entrée de l'extraction évaluation → profil (compétences DÉMONTRÉES)."""
    texte: str = Field(..., min_length=10, description="Compte-rendu d'évaluation à analyser.")
    type: Literal["mission", "performance"] = Field(
        "mission", description="Nature de l'évaluation (source = evaluation_mission | evaluation_performance).")
    top_k: int = Field(1, ge=1, le=5)
    remplacer: bool = Field(True, description="Remplacer les compétences déjà issues de ce type d'évaluation.")


class ProfilCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=120)
    prenom: str | None = Field(None, max_length=120)
    matricule: str | None = Field(None, max_length=32)
    poste_actuel: str | None = Field(None, max_length=200)
    departement_key: str | None = Field(None, max_length=48)
    aspirations: str | None = Field(None, description="Poste visé / souhaits d'évolution.")
    user_id: int | None = Field(None, description="Compte lié ; null = persona synthétique.")
    manager_id: int | None = None
    synthetique: bool = Field(False, description="True = persona de démonstration (donnée fabriquée, à étiqueter).")
    competences: list[ProfilCompetenceIn] = Field(default_factory=list)


class ProfilUpdate(BaseModel):
    """Mise à jour partielle : seuls les champs fournis (non-None) sont appliqués."""
    nom: str | None = Field(None, min_length=1, max_length=120)
    prenom: str | None = None
    poste_actuel: str | None = None
    departement_key: str | None = None
    aspirations: str | None = None
    manager_id: int | None = None


class ProfilSelfUpdate(BaseModel):
    """Édition par le collaborateur de SON PROPRE profil : uniquement les champs
    auto-déclarés (poste visé / aspirations, poste actuel). PAS `departement_key`
    ni `manager_id` (données d'organisation, hors self-service)."""
    aspirations: str | None = Field(None, description="Poste visé / souhaits d'évolution.")
    poste_actuel: str | None = Field(None, max_length=200)


class ProfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None
    nom: str
    prenom: str | None
    matricule: str | None
    poste_actuel: str | None
    departement_key: str | None
    manager_id: int | None
    aspirations: str | None
    synthetique: bool
    created_at: datetime
    competences: list[ProfilCompetenceOut] = Field(default_factory=list)


class ImportResult(BaseModel):
    """Bilan d'un import Excel de profils."""
    importes: int
    ignorees: int
    erreurs: list[str] = []


class MobiliteItem(BaseModel):
    """Passerelle de mobilité : métier du référentiel proche du profil (partage de
    compétences détenues ancrées au graphe)."""
    occupation_id: int
    metier: str
    source: str                # esco | onet | sfia
    competences_partagees: int


class AnnuaireEntry(BaseModel):
    """Vue ANNUAIRE (répertoire limité, sans champ sensible) : accessible à tout
    utilisateur authentifié, y compris COLLAB. Pas de user_id/matricule/manager_id."""
    id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    departement_key: str | None
    competences: list[str] = Field(default_factory=list)


class AncrageResult(BaseModel):
    """Résumé du backfill d'ancrage des compétences détenues au graphe."""
    examinees: int        # compétences non ancrées examinées
    ancrees: int          # nouvellement reliées à une compétence canonique
    categorisees: int     # dont la famille (categorie) a aussi été déduite
