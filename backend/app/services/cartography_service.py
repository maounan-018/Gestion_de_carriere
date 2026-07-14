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

PATH = os.path.join(REPO_ROOT, "config", "departements_metiers.yaml")


def load() -> dict:
    if not os.path.exists(PATH):
        raise FileNotFoundError(f"Cartographie introuvable : {PATH}")
    with open(PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def departements() -> list[dict]:
    return load().get("departements", [])


def get_departement(key: str) -> dict | None:
    return next((d for d in departements() if d.get("key") == key), None)
