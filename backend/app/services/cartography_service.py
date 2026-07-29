#!/usr/bin/env python3
"""
services/cartography_service.py — Cartographie départements → métiers (ÉDITABLE).

RÔLE
    Charge la cartographie BMCI (`config/departements_metiers.yaml`) : départements,
    pôles et métiers-types. Sert de référentiel d'organisation pour générer les
    fiches de poste. Éditable par un accès autorisé (rechargé à chaud).

EMPLACEMENT MVC
    Couche "services" : configuration métier (organisation).
"""

import os

import yaml

from app.core.config import REPO_ROOT
from app.core.yaml_store import write_yaml_atomic

PATH = os.path.join(REPO_ROOT, "config", "departements_metiers.yaml")

_HEADER = (
    "# =====================================================================\n"
    "# CARTOGRAPHIE DÉPARTEMENTS → MÉTIERS — BMCI Gestion des Carrières\n"
    "# =====================================================================\n"
    "# Référentiel édité via l'API (RH/ADMIN) — validé avant écriture. Pilote la\n"
    "# génération des fiches (SYNTHÉTIQUES). Chaque département : key (unique), nom,\n"
    "# pole (optionnel), metiers (liste).\n"
)


def load() -> dict:
    if not os.path.exists(PATH):
        raise FileNotFoundError(f"Cartographie introuvable : {PATH}")
    with open(PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def departements() -> list[dict]:
    return load().get("departements", [])


def get_departement(key: str) -> dict | None:
    return next((d for d in departements() if d.get("key") == key), None)


def _validate(data: dict) -> dict:
    """Valide la cartographie. Lève ValueError si mal formée (protège le fichier)."""
    depts = data.get("departements")
    if not isinstance(depts, list) or not depts:
        raise ValueError("Cartographie invalide : 'departements' manquant ou vide.")
    seen = set()
    for d in depts:
        key, nom = d.get("key"), d.get("nom")
        if not key or key in seen:
            raise ValueError(f"Cartographie invalide : clé de département manquante ou dupliquée ({key}).")
        if not nom:
            raise ValueError(f"Cartographie invalide : 'nom' manquant pour le département {key}.")
        metiers = d.get("metiers", [])
        if not isinstance(metiers, list):
            raise ValueError(f"Cartographie invalide : 'metiers' doit être une liste ({key}).")
        seen.add(key)
    return data


def save(data: dict) -> dict:
    """Valide PUIS persiste la cartographie (écriture atomique). Lève ValueError si
    invalide — dans ce cas le fichier n'est PAS touché."""
    _validate(data)
    write_yaml_atomic(PATH, data, header=_HEADER)
    return data
