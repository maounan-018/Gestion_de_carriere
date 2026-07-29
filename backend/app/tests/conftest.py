#!/usr/bin/env python3
"""
tests/conftest.py — Fixtures pytest partagées.

RÔLE
    - `db` : base SQLite JETABLE par test (services testés en direct).
    - `client` : TestClient sur l'app complète, base temp SEEDÉE (comptes 4 rôles),
      pour les tests d'authentification / RBAC de bout en bout.
    Helpers `auth()` / `anon()` pour piloter la session (cookies HttpOnly + CSRF).

IMPORTANT
    L'engine de l'app est lié à `settings.DB_PATH` À L'IMPORT : on fixe donc
    `DATABASE_PATH` sur une base temporaire AVANT tout import de l'app.
"""

import os
import tempfile
import pathlib

# --- Environnement de test : AVANT tout import de l'app -----------------------
_TMPDIR = tempfile.mkdtemp(prefix="bmci-test-")
os.environ["DATABASE_PATH"] = str(pathlib.Path(_TMPDIR) / "bmci_test.db")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("SEED_DEMO_PASSWORD", "Test-RBAC-2026!")
os.environ["AI_WARMUP_MODELS"] = ""  # pas de préchauffage Ollama pendant les tests

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 — enregistre toutes les tables sur Base.metadata
from app.database.base import Base

DEMO_PASSWORD = os.environ["SEED_DEMO_PASSWORD"]

# email de chaque persona seedé, par rôle logique.
ACCOUNTS = {
    "admin": "admin@bmci.local",
    "rh": "nadia.alami@bmci.local",
    "manager": "jeanmarc.dupont@bmci.local",
    "collab": "marc.bennani@bmci.local",
}


@pytest.fixture(autouse=True)
def _reset_ia_rate_limit():
    """Vide l'état du limiteur de débit IA entre chaque test (singleton module :
    sans ça les compteurs de débit/concurrence fuiraient d'un test à l'autre)."""
    from app.core import rate_limit
    rate_limit._limiter.reset()
    yield
    rate_limit._limiter.reset()


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


@pytest.fixture(scope="session")
def client():
    """TestClient sur l'app complète. Base temp (schéma + comptes seedés).
    Le context-manager déclenche le lifespan → routes réellement montées."""
    from app.database.session import engine, SessionLocal
    from app.database import seed
    Base.metadata.create_all(engine)
    s = SessionLocal()
    try:
        seed.seed_all(s, demo_accounts=True, synthetic_personas=True, password=DEMO_PASSWORD)
    finally:
        s.close()

    from fastapi.testclient import TestClient
    import app.main as m
    with TestClient(m.app) as c:
        yield c


# --- Helpers d'authentification (un seul jeu de cookies par client) -----------
def anon(client) -> None:
    """Repart d'un état NON authentifié (purge les cookies)."""
    client.cookies.clear()


def auth(client, who: str) -> str:
    """Connecte le client comme `who` (admin|rh|manager|collab). Renvoie le token
    CSRF (à passer en en-tête X-CSRF-Token sur les requêtes mutantes)."""
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"email": ACCOUNTS[who], "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def hdr(csrf: str) -> dict:
    """En-tête CSRF pour une requête mutante."""
    return {"X-CSRF-Token": csrf}
