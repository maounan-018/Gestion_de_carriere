#!/usr/bin/env python3
"""
database/init_db.py — Création du schéma : tables ORM + table vectorielle.

RÔLE
    Crée toutes les tables (via Base.metadata) et la table vectorielle sqlite-vec
    `vec_skills` (embeddings des compétences, clé = skills.id). Idempotent :
    peut être appelé à chaque démarrage sans risque.

EMPLACEMENT MVC
    Couche "database" : initialisation du schéma.
"""

import logging

from app.database.base import Base
from app.database.session import engine
from app.core.config import settings
import app.models  # noqa: F401 — enregistre toutes les tables sur Base.metadata

logger = logging.getLogger(__name__)


def _create_vec_table() -> None:
    """Crée les tables vectorielles sqlite-vec (vec0) : compétences ET métiers.
    Tolérant : si l'extension n'est pas chargée, on log et on continue."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_skills USING vec0("
                f"skill_id INTEGER PRIMARY KEY, embedding FLOAT[{settings.EMBED_DIM}])"
            )
            conn.exec_driver_sql(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_occupations USING vec0("
                f"occupation_id INTEGER PRIMARY KEY, embedding FLOAT[{settings.EMBED_DIM}])"
            )
            conn.commit()
        logger.info("Tables vectorielles vec_skills / vec_occupations prêtes (dim %d).", settings.EMBED_DIM)
    except Exception as e:  # noqa: BLE001
        logger.warning("tables vectorielles non créées (%s) — recherche vectorielle indisponible.", e)


def init_db() -> None:
    """Crée le schéma complet (tables relationnelles + table vectorielle)."""
    Base.metadata.create_all(engine)
    _create_vec_table()
    logger.info("Schéma initialisé (%d tables).", len(Base.metadata.tables))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("OK — base initialisée.")
