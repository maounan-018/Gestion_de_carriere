#!/usr/bin/env python3
"""
schemas/skill_matching.py — Contrats d'entrée/sortie du matching profil ↔ poste.

RÔLE
    Forme des données du calcul de correspondance entre les compétences d'un
    collaborateur et celles requises par un poste. La sortie (score, compétences
    couvertes, écarts) est structurée pour être réexploitée par les recommandations
    de parcours et de formation.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    profil_competences: list[str] = Field(
        ..., min_length=1, description="Compétences déclarées du collaborateur."
    )
    poste_texte: str = Field(..., min_length=10, description="Descriptif du poste visé.")
    seuil: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil de pertinence (reranker) au-delà duquel une compétence est jugée couverte.",
    )


class Couverture(BaseModel):
    competence: str
    importance: str | None = None
    couverte_par: str = Field(..., description="Compétence du profil qui couvre l'exigence.")
    similarite: float


class Ecart(BaseModel):
    competence: str
    importance: str | None = None
    meilleure_similarite: float


class MatchResponse(BaseModel):
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score de correspondance pondéré (essentielles > souhaitées).",
    )
    competences_requises: int
    model: str
    couvertes: list[Couverture]
    ecarts: list[Ecart]
