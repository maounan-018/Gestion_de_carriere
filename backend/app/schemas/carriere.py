#!/usr/bin/env python3
"""
schemas/carriere.py — Vue « carrière » enrichie d'un profil.

RÔLE
    Agrège, pour la fiche profil, les éléments de parcours : identité, aspirations,
    compétences (avec niveau), jalons de progression (stations) et avis des pairs.
    Formes natives ; le front compose sa courbe / ses cartes à partir de là.

EMPLACEMENT MVC
    Couche "schemas" : sérialisation (Pydantic).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    periode: str
    titre: str
    description: str | None
    etat: str            # passe | actuel | objectif
    ordre: int


class PeerReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    auteur_nom: str
    auteur_role: str | None
    initiales: str | None
    texte: str
    etoiles: int


class SkillNiveauOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    libelle: str
    categorie: str | None
    niveau: int | None


class ProfilCarriereOut(BaseModel):
    profil_id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    departement_key: str | None
    aspirations: str | None
    bio: str | None = None
    poste_vise: str | None = None
    horizon: str | None = None
    type_evolution: str | None = None
    mobilite_geo: str | None = None
    disponibilite: str | None = None
    competences: list[SkillNiveauOut] = []
    stations: list[StationOut] = []
    avis_pairs: list[PeerReviewOut] = []
