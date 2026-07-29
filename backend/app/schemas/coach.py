#!/usr/bin/env python3
"""
schemas/coach.py — Contrats du Coach Carrière (chat contextualisé).

RÔLE
    Le collaborateur dialogue avec un coach IA qui connaît SON profil (poste,
    aspirations, compétences). Échange conversationnel : un message + l'historique
    récent → une réponse ancrée sur ses données réelles.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CoachMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class CoachRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Question du collaborateur.")
    history: list[CoachMessage] = Field(default_factory=list, description="Tours précédents (contexte).")


class CoachResponse(BaseModel):
    reply: str
    model: str
