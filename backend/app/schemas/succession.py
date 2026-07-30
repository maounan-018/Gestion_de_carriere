#!/usr/bin/env python3
"""
schemas/succession.py — Plan de succession (planification des talents).

RÔLE
    Contrats de la tâche `raisonnement_batch` (qwen3.6) : à partir de la cartographie
    d'un pôle (collaborateurs, compétences, niveaux, aspirations), produire un PLAN
    DE SUCCESSION raisonné (successeurs internes potentiels, préparation, écarts,
    risques). Tâche de RAISONNEMENT lourde → usage batch/RH (pas temps réel).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SuccessionRequest(BaseModel):
    departement_key: str = Field(..., min_length=1, max_length=48,
                                 description="Pôle/département à analyser (ex. 'retail_banking').")


class SuccessionResponse(BaseModel):
    departement_key: str
    effectif: int                 # nb de collaborateurs pris en compte
    plan: str                     # plan de succession rédigé (raisonnement)
    model: str


class SuccessionJobLaunched(BaseModel):
    """Accusé de lancement du job (le client interroge ensuite /succession/jobs/{id})."""
    job_id: str
    status: str = "pending"


class SuccessionJobStatus(BaseModel):
    """État d'un job de succession : `result` peuplé quand `status == done`."""
    status: Literal["pending", "done", "error"]
    result: SuccessionResponse | None = None
    error: str | None = None
