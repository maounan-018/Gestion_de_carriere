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


class SuccesseurOut(BaseModel):
    """Successeur interne pressenti pour un poste clé (calcul déterministe)."""
    nom: str
    poste: str | None
    score: int                    # adéquation au poste clé (0-100)
    readiness: str                # « Prêt » | « 12-24 mois » | « À développer »
    ecarts: list[str] = Field(default_factory=list)   # compétences clés à combler


class PosteCleOut(BaseModel):
    """Poste clé (rôle d'encadrement) et sa relève interne."""
    poste: str
    titulaire: str
    successeurs: list[SuccesseurOut] = Field(default_factory=list)
    risque: bool                  # aucun successeur interne viable


class SuccessionResponse(BaseModel):
    departement_key: str
    effectif: int                 # nb de collaborateurs pris en compte
    postes_cles: int = 0          # nb de postes d'encadrement analysés
    couverts: int = 0             # postes clés avec au moins un successeur viable
    a_risque: int = 0             # postes clés sans successeur
    roles: list[PosteCleOut] = Field(default_factory=list)
    synthese: str = ""            # résumé calculé (texte court)
    plan: str = ""                # rétrocompat (= synthese)
    model: str = "calcul déterministe"


class SuccessionJobLaunched(BaseModel):
    """Accusé de lancement du job (le client interroge ensuite /succession/jobs/{id})."""
    job_id: str
    status: str = "pending"


class SuccessionJobStatus(BaseModel):
    """État d'un job de succession : `result` peuplé quand `status == done`."""
    status: Literal["pending", "done", "error"]
    result: SuccessionResponse | None = None
    error: str | None = None
