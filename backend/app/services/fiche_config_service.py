#!/usr/bin/env python3
"""
services/fiche_config_service.py — Gabarit (typologie) de fiche de poste, ÉDITABLE.

RÔLE
    Charge et valide le gabarit de fiche de poste (`config/fiche_schema.yaml`) qui
    décrit les RUBRIQUES d'une fiche et comment chacune est traitée à l'extraction.
    La typologie d'une fiche pouvant changer, ce gabarit est ÉDITABLE par un
    utilisateur autorisé (RBAC) SANS toucher au code — on le relit à chaque appel,
    donc toute modification prend effet immédiatement.

SÉCURITÉ
    100 % local. La modification du gabarit sera réservée aux rôles autorisés
    (contrôleur protégé), et journalisée (audit) le moment venu.

EMPLACEMENT MVC
    Couche "services" : configuration métier (typologie de fiche).
"""

import os
import logging

import yaml

from app.core.config import REPO_ROOT
from app.core.yaml_store import write_yaml_atomic

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.join(REPO_ROOT, "config", "fiche_schema.yaml")

VALID_KINDS = {"metadata", "freetext", "skill_list", "languages", "kpi"}
VALID_CATEGORIES = {"metier", "comportementale", "transversale", "outil_technologie"}

_HEADER = (
    "# =====================================================================\n"
    "# GABARIT DE FICHE DE POSTE — BMCI Gestion des Carrières\n"
    "# =====================================================================\n"
    "# Édité via l'API (RH/ADMIN) — validé avant écriture. kinds : metadata |\n"
    "# freetext | skill_list | languages | kpi. categorie (freetext/skill_list) :\n"
    "# metier | comportementale | transversale | outil_technologie.\n"
)


def _validate(schema: dict) -> dict:
    """Valide la structure du gabarit. Lève ValueError si mal formé (protège
    l'extraction — et le fichier — contre une édition cassée)."""
    sections = schema.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("Gabarit invalide : 'sections' manquant ou vide.")
    seen = set()
    for s in sections:
        key, kind = s.get("key"), s.get("kind")
        if not key or key in seen:
            raise ValueError(f"Gabarit invalide : clé de section manquante ou dupliquée ({key}).")
        if kind not in VALID_KINDS:
            raise ValueError(f"Gabarit invalide : kind '{kind}' inconnu (section {key}).")
        if kind in ("freetext", "skill_list") and s.get("categorie") not in VALID_CATEGORIES:
            raise ValueError(f"Gabarit invalide : categorie manquante/inconnue pour la section {key}.")
        seen.add(key)
    return schema


def load_schema() -> dict:
    """Charge et VALIDE le gabarit. Lève ValueError si une section est mal formée
    (protège l'extraction contre un gabarit cassé par une édition utilisateur)."""
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Gabarit de fiche introuvable : {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f) or {}
    return _validate(schema)


def save_schema(schema: dict) -> dict:
    """Valide PUIS persiste le gabarit (écriture atomique). Lève ValueError si
    invalide — dans ce cas le fichier n'est PAS touché."""
    _validate(schema)
    write_yaml_atomic(SCHEMA_PATH, schema, header=_HEADER)
    return schema


def get_sections() -> list[dict]:
    """Renvoie la liste des sections du gabarit (rechargé à chaud)."""
    return load_schema().get("sections", [])
