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


class CartoLigne(BaseModel):
    """Une ligne de la heatmap = un pôle/département. `niveaux` est ALIGNÉ sur
    `familles` (même ordre) : `niveaux[i]` = niveau moyen du pôle pour la famille i
    (None si aucune compétence de cette famille dans ce pôle)."""
    departement_key: str
    label: str
    effectif: int
    niveau_moyen: float | None
    niveaux: list[float | None] = []
    people: list[str] = []     # noms des profils du pôle (aperçu, pour le détail)


class CartoMatrix(BaseModel):
    """Cartographie sous forme de MATRICE data-driven : N pôles × M familles, sans
    taxonomie figée. Le front rend `lignes` × `familles` tel quel — ajouter un pôle
    ou une famille en base l'affiche automatiquement."""
    familles: list[str] = []   # colonnes (catégories de compétences présentes)
    lignes: list[CartoLigne] = []


class FamilleCompetence(BaseModel):
    """Vue par FAMILLE de compétences (catégorie) : offre interne détenue vs demande
    des offres ouvertes, avec un signal de tension INDICATIF (heuristique documentée)."""
    famille: str
    detenues: int              # nb de compétences détenues (volume) dans la famille
    profils_couverts: int      # nb de profils ayant ≥1 compétence de la famille
    niveau_moyen: float | None  # niveau moyen (compétences niveautées)
    demande: int               # nb d'attendus des offres OUVERTES dans la famille
    tension: str               # "faible" | "moyenne" | "forte" (demande vs couverture interne)


class PoleEffectif(BaseModel):
    pole: str
    effectif: int


class StatutCount(BaseModel):
    statut: str
    nombre: int


class SyntheseRh(BaseModel):
    """Vue consolidée du tableau de bord RH (au-delà des KPIs simples)."""
    effectif: int
    par_pole: list[PoleEffectif] = []
    candidatures_par_statut: list[StatutCount] = []
    familles_en_tension: int


class HautPotentielItem(BaseModel):
    profil_id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    departement_key: str | None
    score: int                 # proxy de potentiel (0-100), dérivé du niveau moyen
    nb_competences: int
    niveau_moyen: float | None


class VeilleItem(BaseModel):
    """Veille des entretiens par type (réalisés / planifiés / en retard)."""
    key: str                   # "annuels" | "rh"
    label: str
    realises: int
    planifies: int
    en_retard: int


class AlerteItem(BaseModel):
    """Alerte RH dérivée de signaux réels (retard d'entretien, potentiels, mobilité)."""
    kind: str                  # retention | potential | succession
    severity: str              # crit | warn | info
    titre: str
    texte: str
    cta: str
    to_route: str | None = None
