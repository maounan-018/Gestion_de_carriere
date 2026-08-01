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


class EntretienSujet(BaseModel):
    """Personne INCARNÉE par l'IA en mode `entretien_roleplay` (l'intervieweur — manager
    ou RH — mène, l'IA joue le collaborateur). Données de simulation, pas d'accès base."""
    nom: str = Field(..., max_length=120)
    poste: str = Field("", max_length=160)
    aspiration: str | None = Field(None, max_length=300)
    ecarts: list[str] = Field(default_factory=list, description="Compétences à développer.")
    pole: str | None = Field(None, max_length=120)


class CoachRequest(BaseModel):
    # `message` peut être vide pour un TOUR D'OUVERTURE d'entretien (l'IA parle en premier).
    message: str = Field("", max_length=4000, description="Message de l'utilisateur (vide si ouverture).")
    history: list[CoachMessage] = Field(default_factory=list, description="Tours précédents (contexte).")

    # --- Mode conversationnel (défaut : coach carrière agentique, inchangé) ---
    mode: Literal["carriere", "entretien_copilote", "entretien_roleplay"] = Field(
        "carriere", description="carriere = coach agentique ; entretien_* = préparation d'entretien annuel.")
    # Entretien co-pilote (l'utilisateur prépare SON entretien ; l'IA le coache, ancrée sur son profil) :
    section: str | None = Field(None, max_length=120, description="Libellé de la section en cours.")
    focus: str | None = Field(None, max_length=800, description="Consigne de la section pour un tour d'ouverture.")
    ouverture: bool = Field(False, description="True : l'IA ouvre la section ; False : elle réagit à `message`.")
    # Entretien role-play (l'IA incarne un collaborateur) :
    sujet: EntretienSujet | None = Field(None, description="Personne incarnée par l'IA (role-play).")


class CoachResponse(BaseModel):
    reply: str
    model: str
    outils: list[str] = Field(default_factory=list,
                              description="Outils (données réelles) interrogés par le coach agentique.")
