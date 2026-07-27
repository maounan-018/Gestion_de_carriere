#!/usr/bin/env python3
"""
schemas/dashboard.py — Contrats de sortie des tableaux de bord & agrégations RH.

RÔLE
    Formes NATIVES des indicateurs et cartographies calculés côté serveur (KPIs,
    cartographie des compétences par département, hauts potentiels). Le front les
    adapte à ses composants (icônes, tons) via ses mappers.

EMPLACEMENT MVC
    Couche "schemas" : sérialisation (Pydantic).
"""

from __future__ import annotations

from pydantic import BaseModel


class KpiItem(BaseModel):
    key: str
    value: int
    label: str
    hint: str | None = None


class DashboardKpis(BaseModel):
    scope: str                 # "rh" | "manager"
    kpis: list[KpiItem]


class CartoTopCompetence(BaseModel):
    libelle: str
    effectif: int              # nb de profils du département détenant la compétence
    niveau_moyen: float | None


class CartoDepartement(BaseModel):
    departement_key: str
    effectif: int              # nb de profils rattachés
    niveau_moyen: float | None  # niveau moyen (1-5) toutes compétences confondues
    nb_competences: int        # nb de compétences distinctes détenues
    top_competences: list[CartoTopCompetence] = []


class HautPotentielItem(BaseModel):
    profil_id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    departement_key: str | None
    score: int                 # proxy de potentiel (0-100), dérivé du niveau moyen
    nb_competences: int
    niveau_moyen: float | None
