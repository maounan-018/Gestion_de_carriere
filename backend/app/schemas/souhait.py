#!/usr/bin/env python3
"""
schemas/souhait.py — Contrats d'entrée/sortie d'un Souhait d'évolution.

RÔLE
    Le collaborateur crée/édite ses souhaits (poste visé, mission) et peut les
    POUSSER à son manager. `SouhaitRecuOut` enrichit la sortie des informations du
    collaborateur émetteur, pour la vue « souhaits reçus » du manager.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

KindSouhait = Literal["carriere", "mission"]
StatutSouhait = Literal["brouillon", "pousse", "en_discussion", "accorde", "refuse"]


class SouhaitCreate(BaseModel):
    titre: str = Field(..., min_length=1, max_length=200)
    kind: KindSouhait = "carriere"
    horizon: str | None = Field(None, max_length=32, description="Ex : « 6 mois », « 1-2 ans ».")
    description: str | None = None
    pushed: bool = Field(False, description="Pousser immédiatement au manager.")


class SouhaitUpdate(BaseModel):
    """Mise à jour partielle (le collaborateur édite ; RH/manager peut faire évoluer le statut)."""
    titre: str | None = Field(None, min_length=1, max_length=200)
    kind: KindSouhait | None = None
    horizon: str | None = Field(None, max_length=32)
    description: str | None = None
    statut: StatutSouhait | None = None
    pushed: bool | None = None


class SouhaitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profil_id: int
    titre: str
    kind: str
    horizon: str | None
    description: str | None
    statut: str
    pushed: bool
    created_at: datetime
    decided_at: datetime | None


class SouhaitRecuOut(SouhaitOut):
    """Souhait poussé, vu par le manager : + identité du collaborateur émetteur."""
    membre_nom: str
    membre_prenom: str | None = None
    membre_matricule: str | None = None
