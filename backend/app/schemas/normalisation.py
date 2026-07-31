#!/usr/bin/env python3
"""
schemas/normalisation.py — Normalisation de libellés de compétences.

RÔLE
    Canonicalise une liste de libellés bruts (variantes de casse/orthographe,
    synonymes, franglais) en formes CANONIQUES regroupées. Utile pour nettoyer /
    dédoublonner des compétences (import, profil) avant de les stocker ou matcher.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NormaliseRequest(BaseModel):
    libelles: list[str] = Field(..., min_length=1, max_length=60,
                                description="Libellés bruts à canonicaliser (1 à 60).")


class NormaliserCibleRequest(BaseModel):
    """Une saisie libre (objectif/intitulé de poste) à structurer."""
    texte: str = Field(..., min_length=1, max_length=500,
                       description="Saisie libre à normaliser (fautes/annotations tolérées).")


class NormaliserCibleResponse(BaseModel):
    """Saisie structurée : intitulé canonique + confiance (clair / ambigu / indisponible)."""
    intitule: str
    confiance: Literal["clair", "ambigu", "indisponible"]
    model: str


class NormaliseGroupe(BaseModel):
    canonique: str                       # forme canonique retenue pour le groupe
    variantes: list[str] = []            # libellés d'entrée regroupés sous cette forme


class NormaliseResponse(BaseModel):
    groupes: list[NormaliseGroupe]
    model: str
