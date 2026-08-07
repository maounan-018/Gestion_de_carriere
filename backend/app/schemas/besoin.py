#!/usr/bin/env python3
"""schemas/besoin.py — E/S du besoin de recrutement (manager → HRBP)."""
from datetime import datetime

from pydantic import BaseModel, Field


class BesoinCreate(BaseModel):
    """Le manager exprime un besoin sur un poste (fiche de référence + description)."""
    fiche_id: int | None = Field(None, description="Fiche de poste de référence (menu déroulant).")
    poste: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=4000,
                                    description="Contexte / justification du besoin.")


class BesoinRefus(BaseModel):
    motif: str | None = Field(None, max_length=400)


class BesoinContact(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class BesoinPublier(BaseModel):
    """Ajustements HRBP à la publication (sinon dérivés du besoin)."""
    titre: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=4000)
    localisation: str | None = Field(None, max_length=120)


class BesoinOut(BaseModel):
    id: int
    manager_user_id: int
    manager_nom: str | None = None
    fiche_id: int | None = None
    poste: str
    description: str | None = None
    statut: str
    offre_id: int | None = None
    motif_refus: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
