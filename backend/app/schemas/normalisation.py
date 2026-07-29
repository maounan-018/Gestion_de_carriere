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

from pydantic import BaseModel, Field


class NormaliseRequest(BaseModel):
    libelles: list[str] = Field(..., min_length=1, max_length=60,
                                description="Libellés bruts à canonicaliser (1 à 60).")


class NormaliseGroupe(BaseModel):
    canonique: str                       # forme canonique retenue pour le groupe
    variantes: list[str] = []            # libellés d'entrée regroupés sous cette forme


class NormaliseResponse(BaseModel):
    groupes: list[NormaliseGroupe]
    model: str
