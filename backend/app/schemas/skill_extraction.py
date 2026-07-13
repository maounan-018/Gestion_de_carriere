#!/usr/bin/env python3
"""
schemas/skill_extraction.py — Contrats d'entrée/sortie de l'extraction de compétences.

RÔLE
    Définit la forme EXACTE des données échangées par l'API d'extraction. La sortie
    est structurée et reliée au graphe (chaque compétence extraite -> compétences
    canoniques ESCO/O*NET), donc directement réexploitable par le matching, les
    recommandations et l'entretien annuel.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic), sans logique métier.
"""

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=10,
                      description="Descriptif de poste, de mission ou d'offre à analyser.")
    top_k: int = Field(1, ge=1, le=5,
                       description="Nombre de compétences canoniques rapprochées par compétence extraite.")


class MatchedSkill(BaseModel):
    """Compétence canonique du graphe rapprochée d'une compétence extraite."""
    skill_id: int
    label_fr: str
    label_en: str
    skill_type: str
    distance: float
    score: float
    rerank_score: float | None = None  # pertinence cross-encoder (si reranker actif)


class ExtractedSkill(BaseModel):
    raw: str = Field(..., description="Libellé de compétence tel qu'extrait du texte.")
    category: str | None = Field(None, description="savoir-faire | savoir | savoir-être")
    importance: str | None = Field(None, description="essentielle | souhaitée")
    matches: list[MatchedSkill] = Field(default_factory=list,
                                        description="Compétences canoniques du graphe rapprochées.")


class ExtractResponse(BaseModel):
    job_title: str | None = None
    model: str = Field(..., description="Modèle IA local ayant produit l'extraction.")
    skills: list[ExtractedSkill]
