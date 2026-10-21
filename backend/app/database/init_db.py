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

import app.models  # noqa: F401 — enregistre toutes les tables sur Base.metadata
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine

logger = logging.getLogger(__name__)


def _create_vec_table() -> None:
    """Crée les tables vectorielles (embeddings compétences ET métiers), selon le
    dialecte : sqlite-vec (vec0) en local, pgvector (vector + index HNSW) sur
    Supabase/Postgres. Tolérant : si l'extension n'est pas chargée, on log et on
    continue (la recherche vectorielle se dégrade sans faire tomber le démarrage)."""
    dim = settings.EMBED_DIM
    try:
        if engine.dialect.name == "postgresql":
            # pgvector : colonne vector(dim) + index HNSW cosine (aligné sur
            # l'opérateur <=> utilisé par database/vector_search.py). FK vers les
            # tables sources (intégrité : un embedding référence toujours une ligne).
            with engine.connect() as conn:
                conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
                conn.exec_driver_sql(
                    f"CREATE TABLE IF NOT EXISTS vec_skills ("
                    f"skill_id INTEGER PRIMARY KEY REFERENCES skills(id) ON DELETE CASCADE, "
                    f"embedding vector({dim}) NOT NULL)"
                )
                conn.exec_driver_sql(
                    f"CREATE TABLE IF NOT EXISTS vec_occupations ("
                    f"occupation_id INTEGER PRIMARY KEY REFERENCES occupations(id) ON DELETE CASCADE, "
                    f"embedding vector({dim}) NOT NULL)"
                )
                # Documents personnels du Coach (RAG par utilisateur) : embeddings par chunk.
                conn.exec_driver_sql(
                    f"CREATE TABLE IF NOT EXISTS vec_coach_docs ("
                    f"chunk_id INTEGER PRIMARY KEY REFERENCES coach_document_chunks(id) ON DELETE CASCADE, "
                    f"embedding vector({dim}) NOT NULL)"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_vec_skills_hnsw ON vec_skills "
                    "USING hnsw (embedding vector_cosine_ops)"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_vec_occupations_hnsw ON vec_occupations "
                    "USING hnsw (embedding vector_cosine_ops)"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_vec_coach_docs_hnsw ON vec_coach_docs "
                    "USING hnsw (embedding vector_cosine_ops)"
                )
                conn.commit()
            logger.info("Tables vectorielles pgvector prêtes (vector(%d) + HNSW).", dim)
        else:
            # sqlite-vec : tables virtuelles vec0 (défaut local).
            with engine.connect() as conn:
                conn.exec_driver_sql(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_skills USING vec0("
                    f"skill_id INTEGER PRIMARY KEY, embedding FLOAT[{dim}])"
                )
                conn.exec_driver_sql(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_occupations USING vec0("
                    f"occupation_id INTEGER PRIMARY KEY, embedding FLOAT[{dim}])"
                )
                conn.exec_driver_sql(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_coach_docs USING vec0("
                    f"chunk_id INTEGER PRIMARY KEY, embedding FLOAT[{dim}])"
                )
                conn.commit()
            logger.info(
                "Tables vectorielles prêtes (skills / occupations / coach_docs, dim %d).", dim
            )
    except Exception as e:
        logger.warning(
            "tables vectorielles non créées (%s) — recherche vectorielle indisponible.", e
        )


def init_db() -> None:
    """Crée le schéma complet (tables relationnelles + table vectorielle)."""
    Base.metadata.create_all(engine)
    _create_vec_table()
    logger.info("Schéma initialisé (%d tables).", len(Base.metadata.tables))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("OK — base initialisée.")
