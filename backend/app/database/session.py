#!/usr/bin/env python3
"""
database/session.py — Moteur SQLAlchemy, sessions et extension vectorielle.

RÔLE
    Crée le moteur SQLite, charge l'extension sqlite-vec sur CHAQUE connexion
    (recherche vectorielle DANS SQLite, aucune base externe), et fournit la
    dépendance FastAPI `get_db` (session par requête, fermée proprement).

SÉCURITÉ / CNDP
    Tout reste local : base fichier SQLite + vecteurs sqlite-vec. En production,
    on pourra pointer vers PostgreSQL + pgvector sans changer les modèles.

EMPLACEMENT MVC
    Couche "database" : fabrique de sessions.
"""

import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# check_same_thread=False : le serveur ASGI peut réutiliser la connexion entre threads.
engine = create_engine(
    f"sqlite:///{settings.DB_PATH}",
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


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session, future=True)


def get_db():
    """Dépendance FastAPI : ouvre une session par requête et la ferme à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
