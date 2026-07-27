#!/usr/bin/env python3
"""
schemas/candidature.py — Contrats d'entrée/sortie d'une Candidature.

RÔLE
    Relie un Profil (candidat) à une Offre. À la création, le service confronte les
    compétences DÉTENUES aux ATTENDUS de l'offre → `score` (0-100) + snapshot des
    écarts (traçabilité). ⚠️ Le score est INDICATIF, pas un filtre : un candidat
    < 100 % peut être RETENU — la décision reste humaine (`statut` + `decided_by`).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatutCandidature = Literal["deposee", "en_evaluation", "retenue", "rejetee", "retiree"]
# Statut d'un attendu vis-à-vis du profil, dans le snapshot d'évaluation.
StatutAttendu = Literal["couverte", "manquante", "niveau_insuffisant"]


class CandidatureCreate(BaseModel):
    offre_id: int
    profil_id: int
    motivation: str | None = Field(None, description="Note libre du candidat (optionnel).")
    # Le score n'est JAMAIS fourni en entrée : il est calculé côté serveur.


class CandidatureDecision(BaseModel):
    """Décision HUMAINE sur une candidature (retenue possible même si score < 100 %).
    `decided_by` n'est PAS dans l'entrée : le serveur l'impose depuis la session."""
    statut: Literal["en_evaluation", "retenue", "rejetee"]


class AttenduEvalue(BaseModel):
    """Ligne du snapshot d'évaluation (un attendu de l'offre confronté au profil)."""
    competence: str
    importance: str
    niveau_requis: int | None = None
    statut: StatutAttendu
    couverte_par: str | None = None
    niveau_detenu: int | None = None
    skill_id: int | None = None


class EvaluationOut(BaseModel):
    """Snapshot complet du calcul de score (traçabilité)."""
    score: int
    methode: str
    attendus_total: int
    couvertes: list[AttenduEvalue] = Field(default_factory=list)
    ecarts: list[AttenduEvalue] = Field(default_factory=list)


class CandidatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    offre_id: int
    profil_id: int
    statut: str
    score: float | None
    motivation: str | None
    created_at: datetime
    reevaluated_at: datetime | None = None  # dernière réévaluation (None si jamais réévaluée)
    decided_at: datetime | None
    decided_by: int | None
    evaluation: EvaluationOut | None = Field(
        None, description="Snapshot des écarts au moment de l'évaluation (traçabilité).")


class CandidatureMineOut(BaseModel):
    """« Mes candidatures » : candidature + titre/type de l'offre (jointure) pour
    l'écran collaborateur, sans avoir à re-fetcher chaque offre."""
    id: int
    statut: str
    score: float | None
    created_at: datetime
    offre_titre: str
    offre_type: str
