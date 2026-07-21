#!/usr/bin/env python3
"""
tests/conftest.py — Fixtures pytest partagées.

RÔLE
    Fournit une base SQLite JETABLE et isolée par test (fichier temporaire),
    créée depuis les modèles ORM (`Base.metadata.create_all`). Les tables
    vectorielles sqlite-vec ne sont PAS mappées à l'ORM (créées à part en SQL) :
    inutiles ici, donc pas besoin de l'extension pour tester la couche métier.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 — enregistre toutes les tables sur Base.metadata
from app.database.base import Base


@pytest.fixture()
def db(tmp_path) -> Session:
    """Session SQLAlchemy sur une base SQLite temporaire, neuve à chaque test."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False,
                               class_=Session, future=True)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
