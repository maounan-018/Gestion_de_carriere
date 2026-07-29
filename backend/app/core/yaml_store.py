#!/usr/bin/env python3
"""
core/yaml_store.py — Écriture atomique de fichiers YAML de configuration.

RÔLE
    Persiste un référentiel YAML éditable (gabarit de fiche, cartographie) SANS
    risque de corruption : écrit dans un fichier temporaire du même dossier puis
    `os.replace` (atomique sur le même volume). Un plantage en cours d'écriture
    laisse donc l'ancien fichier intact. Un en-tête de commentaire optionnel garde
    le fichier auto-documenté (safe_dump ne conserve pas les commentaires d'origine).

EMPLACEMENT MVC
    Couche "core" : utilitaire d'infrastructure, sans logique métier.
"""

from __future__ import annotations

import os

import yaml


def write_yaml_atomic(path: str, data: dict, *, header: str = "") -> None:
    """Écrit `data` en YAML sur `path` de façon atomique (temp + replace).
    `header` : commentaire (lignes commençant par '#') écrit en tête, optionnel."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        if header:
            f.write(header if header.endswith("\n") else header + "\n")
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    os.replace(tmp, path)   # atomique : l'ancien fichier reste intact en cas d'échec avant
