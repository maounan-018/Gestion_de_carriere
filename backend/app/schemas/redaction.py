#!/usr/bin/env python3
"""
schemas/redaction.py — Aide à la rédaction (résumé / reformulation).

RÔLE
    Contrats de la tâche `redaction` (mistral-nemo) : résumer ou reformuler un texte
    (bilan d'entretien, aspiration, note) en français clair et professionnel, sans
    trahir le sens ni inventer.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RedactionRequest(BaseModel):
    texte: str = Field(..., min_length=1, max_length=8000, description="Texte source à traiter.")
    mode: Literal["resume", "reformulation"] = Field(
        "resume", description="resume = synthèse concise ; reformulation = même sens, plus clair."
    )
    consignes: str | None = Field(
        None, max_length=500, description="Consigne optionnelle (ton, longueur, angle)."
    )


class RedactionResponse(BaseModel):
    texte: str
    mode: str
    model: str
