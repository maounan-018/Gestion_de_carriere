#!/usr/bin/env python3
"""
schemas/offre.py — Contrats d'entrée/sortie d'une Offre (dérivée d'une Fiche).

RÔLE
    Forme des données d'une opportunité à pourvoir (offre de poste RH, ou
    mission/projet/gig manager) et de ses ATTENDUS overridables. À la création,
    si une `fiche_id` de référence est fournie, les compétences de la Fiche sont
    COPIÉES en attendus (`source="fiche"`) puis éditables au niveau de l'offre —
    la Fiche de référence, elle, n'est jamais modifiée.

    Le `score` d'une candidature s'évalue contre ces attendus (cf. candidature).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Miroirs des constantes de models.offre (validation d'entrée).
TypeOffre = Literal["offre_poste", "mission", "projet", "gig"]
StatutOffre = Literal["brouillon", "ouverte", "pourvue", "fermee", "annulee"]
Importance = Literal["essentielle", "souhaitee"]
SourceComp = Literal["fiche", "ajout_offre"]


class OffreCompetenceIn(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=300)
    categorie: str | None = Field(None, max_length=24,
                                  description="metier | comportementale | transversale | outil_technologie")
    skill_id: int | None = Field(None, description="Ancrage graphe (compétence canonique ESCO/O*NET/SFIA).")
    skill_label_fr: str | None = Field(None, max_length=300)
    importance: Importance = Field("essentielle", description="essentielle (bloquante) | souhaitee (bonus).")
    niveau_requis: int | None = Field(None, ge=1, le=5, description="Niveau requis 1-5 (aligné SFIA).")
    source: SourceComp = Field("ajout_offre", description="fiche (héritée) | ajout_offre (ajoutée au niveau offre).")


class OffreCompetenceOut(OffreCompetenceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rerank_score: float | None = None


class OffreCompetenceUpdate(BaseModel):
    """Override d'un attendu au niveau de l'offre (partiel, champs non-None seulement)."""
    libelle: str | None = Field(None, min_length=1, max_length=300)
    categorie: str | None = None
    importance: Importance | None = None
    niveau_requis: int | None = Field(None, ge=1, le=5)


class OffreCreate(BaseModel):
    titre: str = Field(..., min_length=1, max_length=200)
    fiche_id: int | None = Field(None, description="Fiche de référence dont dérive l'offre (attendus copiés).")
    heriter_competences: bool = Field(True, description="Copier les compétences de la Fiche comme attendus (si fiche_id).")
    type: TypeOffre = "offre_poste"
    description: str | None = None
    perimetre_bmci: str | None = Field(None, max_length=160)
    departement_key: str | None = Field(None, max_length=48)
    statut: StatutOffre = "brouillon"
    created_by: int | None = Field(None, description="Utilisateur qui pousse l'offre (RH ou manager).")
    manager_id: int | None = Field(None, description="Manager concerné (notification).")
    date_ouverture: datetime | None = None
    date_cloture: datetime | None = None
    synthetique: bool = Field(False, description="True = donnée de démonstration fabriquée (à étiqueter).")
    competences: list[OffreCompetenceIn] = Field(
        default_factory=list,
        description="Attendus ajoutés explicitement (en plus de ceux hérités de la Fiche).")


class OffreUpdate(BaseModel):
    """Mise à jour partielle de l'offre (jamais la Fiche de référence)."""
    titre: str | None = Field(None, min_length=1, max_length=200)
    type: TypeOffre | None = None
    description: str | None = None
    perimetre_bmci: str | None = Field(None, max_length=160)
    departement_key: str | None = Field(None, max_length=48)
    statut: StatutOffre | None = Field(None, description="Transition de statut (dates ouverture/clôture posées auto).")
    manager_id: int | None = None
    date_ouverture: datetime | None = None
    date_cloture: datetime | None = None


class OffreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fiche_id: int | None
    type: str
    titre: str
    description: str | None
    perimetre_bmci: str | None
    departement_key: str | None
    statut: str
    created_by: int | None
    manager_id: int | None
    date_ouverture: datetime | None
    date_cloture: datetime | None
    synthetique: bool
    created_at: datetime
    competences: list[OffreCompetenceOut] = Field(default_factory=list)
