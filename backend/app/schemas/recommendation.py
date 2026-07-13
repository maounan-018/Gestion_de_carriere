#!/usr/bin/env python3
"""
schemas/recommendation.py — Contrats de la recommandation formation & parcours.

RÔLE
    Forme des données de la recommandation : à partir des compétences attendues
    d'un poste visé (nos 3 socles), les compétences à développer (écarts enrichis)
    + les passerelles métiers + un plan de développement rédigé. Structuré pour
    alimenter l'écran collaborateur et les mini-applications.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    profil_competences: list[str] = Field(..., min_length=1,
                                          description="Compétences actuelles du collaborateur.")
    poste_texte: str = Field(..., min_length=10, description="Descriptif du poste visé.")
    seuil: float = Field(0.5, ge=0.0, le=1.0,
                         description="Seuil de couverture (reranker) en-deçà duquel une compétence est un écart.")


class EtapeFormation(BaseModel):
    competence: str
    importance: str | None = None
    type: str | None = None
    niveau_sfia: int | None = Field(None, description="Niveau SFIA visé (1..7) si compétence numérique.")
    description: str | None = None
    sous_competences: list[str] = Field(default_factory=list,
                                        description="Sous-compétences (graphe) = étapes concrètes d'apprentissage.")


class Passerelle(BaseModel):
    metier: str
    source: str
    pertinence: float = Field(..., ge=0.0, le=1.0,
                              description="Proximité sémantique du métier avec le poste visé (0..1).")


class RecommendationResponse(BaseModel):
    poste_vise: str | None = None
    score_actuel: int = Field(..., ge=0, le=100)
    modele_extraction: str
    modele_conseil: str
    competences_a_developper: list[EtapeFormation]
    passerelles_metiers: list[Passerelle]
    plan_developpement: str
