#!/usr/bin/env python3
"""
schemas/formation.py — Contrat de sortie d'une Formation (catalogue synthétique).

RÔLE
    Expose une formation du catalogue. Les `tags` sont stockés en CSV et renvoyés
    en liste. `synthetique` rappelle que le catalogue est fabriqué (démo).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titre: str
    provider: str | None
    duree: str | None
    niveau: str | None
    domaine: str | None
    tags: list[str] = []
    skill_cible: str | None
    synthetique: bool

    @field_validator("tags", mode="before")
    @classmethod
    def _split_tags(cls, v):
        """Accepte le CSV stocké en base et le renvoie en liste."""
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v


class FormationGenerationRequest(BaseModel):
    competence: str = Field(
        ..., min_length=2, description="Compétence à développer (cible de la formation)."
    )
    persister: bool = Field(False, description="Ajouter la formation générée au catalogue.")


class FormationGeneree(BaseModel):
    """Formation SYNTHÉTIQUE générée (proposition pédagogique). `id` présent si persistée."""

    titre: str
    organisme: str | None = None
    duree: str | None = None
    niveau: str | None = None
    domaine: str | None = None
    skill_cible: str | None = None
    objectifs: list[str] = []
    modules: list[str] = []
    tags: list[str] = []
    synthetique: bool = True
    id: int | None = None
