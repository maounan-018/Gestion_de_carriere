"""schemas/fiche.py — Lecture des fiches de poste (sélecteur « Publier une offre »).

Exposition minimale des fiches générées : liste (pour le sélecteur de poste) et
détail (mission, activités, compétences attendues) affiché quand une fiche est
choisie, avant d'en dériver une offre.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FicheCompetenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    libelle: str
    categorie: str | None = None


class FicheListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    intitule_poste: str
    departement_key: str
    perimetre_bmci: str
    famille_metier: str | None = None


class FicheDetailOut(FicheListItem):
    mission: str | None = None
    activites_principales: str | None = None
    langues: str | None = None
    indicateurs_performances: str | None = None
    competences: list[FicheCompetenceOut] = []
