#!/usr/bin/env python3
"""
database/session.py — Moteur SQLAlchemy, sessions et extension vectorielle.

RÔLE
    Fabrique le moteur SQLAlchemy selon le DIALECTE cible (piloté par
    `settings.sqlalchemy_url`) et fournit la dépendance FastAPI `get_db` :
      - SQLite (dev/local) : charge l'extension sqlite-vec sur chaque connexion
        (recherche vectorielle DANS SQLite) + PRAGMA de concurrence/latence.
      - PostgreSQL / Supabase (prod) : pool robuste pour base DISTANTE (pre_ping,
        recycle) + enregistrement du type `vector` (pgvector) par connexion.

SÉCURITÉ / CNDP
    Dev : tout reste local (fichier SQLite + sqlite-vec). Prod : Postgres + pgvector
    managé (Supabase), URL/secret hors du code (DATABASE_URL). Les modèles ORM sont
    identiques dans les deux cas — seuls le moteur et la recherche vectorielle changent.

EMPLACEMENT MVC
    Couche "database" : fabrique de sessions.
"""

import os
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

_URL = settings.sqlalchemy_url


if settings.is_sqlite:
    # check_same_thread=False : le serveur ASGI peut réutiliser la connexion entre threads.
    engine = create_engine(
        _URL,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _load_sqlite_vec(dbapi_conn, _record):
        """Charge l'extension sqlite-vec sur chaque nouvelle connexion SQLite.
        Si elle est absente, on log un avertissement mais on ne bloque pas le boot
        (les fonctions non-vectorielles restent utilisables)."""
        try:
            import sqlite_vec
            dbapi_conn.enable_load_extension(True)
            sqlite_vec.load(dbapi_conn)
            dbapi_conn.enable_load_extension(False)
        except Exception as e:  # noqa: BLE001
            logger.warning("sqlite-vec non chargé (%s) — recherche vectorielle indisponible.", e)

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        """Réglages SQLite pour la concurrence et la latence (modèle sync threadpoolé :
        plusieurs threads accèdent à la base en parallèle).
          - WAL : les lecteurs ne sont plus bloqués par un writer (moins de « locked »).
          - busy_timeout : attend au lieu d'échouer immédiatement en cas de verrou.
          - synchronous=NORMAL : durable en WAL, nettement plus rapide que FULL.
          - cache/temp_store : cache page en RAM + tables temporaires en mémoire.
        journal_mode=WAL est persistant (posé une fois) ; les autres sont par-connexion.
        NB : PRAGMA foreign_keys=ON (intégrité référentielle, OFF par défaut en SQLite)
        n'est PAS activé ici : c'est une correction d'INTÉGRITÉ (pas de perf) qui doit
        d'abord garantir la validité de toutes les FK (ex. profil_competences.skill_id) ;
        à traiter dans un lot correctness dédié pour éviter toute régression."""
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA temp_store=MEMORY")
            cur.execute("PRAGMA cache_size=-16000")   # ~16 Mo de cache page (valeur en Kio)
        finally:
            cur.close()

else:
    # PostgreSQL / Supabase : base DISTANTE derrière un pooler (pgBouncer).
    #  - pool_pre_ping : élimine les connexions coupées par le pooler avant réutilisation.
    #  - pool_recycle : borne la durée de vie d'une connexion (évite les coupures serveur).
    #  - prepare_threshold=None : désactive les prepared statements côté psycopg, requis
    #    en mode « transaction » du pooler Supabase (port 6543) qui ne les supporte pas.
    engine = create_engine(
        _URL,
        pool_pre_ping=True,
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        connect_args={"prepare_threshold": None},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _register_pgvector(dbapi_conn, _record):
        """Enregistre le type `vector` (pgvector) sur chaque connexion, pour lier
        directement des vecteurs Python. Tolérant : si l'extension `vector` n'est pas
        encore créée (avant P1), on log sans bloquer le boot."""
        try:
            from pgvector.psycopg import register_vector
            register_vector(dbapi_conn)
        except Exception as e:  # noqa: BLE001
            logger.warning("pgvector non enregistré (%s) — recherche vectorielle indisponible.", e)


logger.info("Moteur SQLAlchemy : dialecte=%s", settings.db_dialect)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session, future=True)


def get_db():
    """Dépendance FastAPI : ouvre une session par requête et la ferme à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
