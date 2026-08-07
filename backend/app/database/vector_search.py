#!/usr/bin/env python3
"""
database/vector_search.py — Recherche vectorielle KNN, dialecte-agnostique.

RÔLE
    Unifie la recherche des k plus proches voisins entre les deux backends :
      - SQLite (dev)  : extension sqlite-vec (table virtuelle vec0), contrainte
                        `embedding MATCH :q AND k = :k`, colonne `distance` (L2).
      - PostgreSQL    : pgvector, `ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k`
        (Supabase)      (distance cosinus `<=>`), sur une table `vec_*` classique
                        avec une colonne `embedding vector(N)`.

    Dans les deux cas, le vecteur requête est passé en paramètre `:q` sous forme de
    chaîne JSON (`json.dumps(vec)`) — format lu tel quel par sqlite-vec ET accepté en
    entrée texte par pgvector via CAST(:q AS vector). Seule la forme de la requête
    change ; les colonnes projetées et l'alias `distance` sont identiques.

EMPLACEMENT MVC
    Couche "database" : brique SQL réutilisable, sans logique métier.
"""

from __future__ import annotations

from app.core.config import settings


def knn_sql(select_cols: str, vec_table: str, vec_alias: str, join: str,
            *, extra_where: str = "") -> str:
    """Construit la requête KNN pour le dialecte courant.

    - select_cols : colonnes projetées (SANS la distance, ajoutée ici sous l'alias
      `distance`). Ex. "o.id, o.label_fr, o.source".
    - vec_table / vec_alias : table des vecteurs et son alias. Ex. "vec_skills", "vk".
    - join : le reste du FROM après la table vecteur. Ex.
      "skills s ON s.id = vk.skill_id".
    - extra_where : filtres additionnels déjà écrits pour le dialecte courant
      (voir `bool_true`), sans le mot-clé WHERE. Ex. "s.canonical" (Postgres).

    Paramètres liés attendus à l'exécution : `:q` (json.dumps du vecteur) et `:k`.
    """
    if settings.is_sqlite:
        where = f"WHERE {vec_alias}.embedding MATCH :q AND k = :k"
        if extra_where:
            where += f" AND {extra_where}"
        return (f"SELECT {select_cols}, {vec_alias}.distance "
                f"FROM {vec_table} {vec_alias} JOIN {join} "
                f"{where} ORDER BY {vec_alias}.distance")
    # PostgreSQL / pgvector
    where = f"WHERE {extra_where}" if extra_where else ""
    return (f"SELECT {select_cols}, ({vec_alias}.embedding <=> CAST(:q AS vector)) AS distance "
            f"FROM {vec_table} {vec_alias} JOIN {join} "
            f"{where} ORDER BY distance LIMIT :k")


def bool_true(column: str) -> str:
    """Prédicat booléen VRAI portable : `col = 1` en SQLite (0/1), `col` en Postgres
    (vrai booléen). Ex. filtre des compétences canoniques."""
    return f"{column} = 1" if settings.is_sqlite else column
