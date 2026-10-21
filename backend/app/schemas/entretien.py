#!/usr/bin/env python3
"""
schemas/entretien.py — E/S de la synthèse de préparation d'entretien.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SyntheseEntretienIn(BaseModel):
    """Synthèse de la simulation à conserver (texte brut)."""

    synthese: str = Field(..., min_length=1, max_length=20000)


class SyntheseEntretienOut(BaseModel):
    synthese: str
    enregistre_le: str
