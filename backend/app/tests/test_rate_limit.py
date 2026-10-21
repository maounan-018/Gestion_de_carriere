#!/usr/bin/env python3
"""
tests/test_rate_limit.py — Limitation de débit des endpoints IA.

Deux niveaux :
  - unitaire : le `IARateLimiter` (fenêtre glissante + concurrence, par user) ;
  - e2e HTTP : un endpoint IA renvoie 429 (+ Retry-After) au-delà du seuil, et
    l'abus est journalisé (audit). Rédaction monkeypatchée -> pas d'Ollama.
"""

from sqlalchemy import select

from app.core.rate_limit import IARateLimiter
from app.tests.conftest import auth, hdr

# ------------------------------------------------------------------ Unitaire


def test_limiter_debit_fenetre():
    """Au-delà de N appels dans la fenêtre : refus + retry ; autre user épargné."""
    lim = IARateLimiter(max_per_window=2, window_seconds=60, max_concurrent=10)
    assert lim.acquire(1)[0] is True
    assert lim.acquire(1)[0] is True
    ok, retry = lim.acquire(1)
    assert ok is False and retry >= 1
    assert lim.acquire(2)[0] is True  # cloisonné par utilisateur


def test_limiter_concurrence():
    """Une requête IA en vol par user (max_concurrent=1) : la 2e simultanée est
    refusée, puis autorisée après libération."""
    lim = IARateLimiter(max_per_window=100, window_seconds=60, max_concurrent=1)
    assert lim.acquire(1)[0] is True
    assert lim.acquire(1)[0] is False  # une 2e en parallèle -> refus
    lim.release(1)
    assert lim.acquire(1)[0] is True  # après release -> ok


def test_limiter_reset():
    """reset() vide l'état (débit + concurrence)."""
    lim = IARateLimiter(max_per_window=1, window_seconds=60, max_concurrent=10)
    assert lim.acquire(1)[0] is True
    assert lim.acquire(1)[0] is False
    lim.reset()
    assert lim.acquire(1)[0] is True


# ------------------------------------------------------------------ e2e HTTP


def test_ia_rate_limit_bloque_et_audite(client, monkeypatch):
    """Au-delà du seuil, l'endpoint IA renvoie 429 + Retry-After, et journalise
    un évènement RATE_LIMITED (détection d'abus)."""
    from app.core import rate_limit
    from app.database.session import SessionLocal
    from app.models.audit_log import AuditEventType, AuditLog
    from app.services import redaction_service

    # Rédaction instantanée (aucune génération Ollama pendant le test).
    monkeypatch.setattr(
        redaction_service,
        "rediger",
        lambda texte, mode, consignes=None: {"texte": "ok", "mode": mode, "model": "test"},
    )
    # Fenêtre serrée : 2 requêtes autorisées, la 3e refusée.
    monkeypatch.setattr(rate_limit._limiter, "max_per_window", 2)

    csrf = auth(client, "collab")
    body = {"texte": "Un bilan à résumer pour le test.", "mode": "resume"}
    r1 = client.post("/api/redaction", json=body, headers=hdr(csrf))
    r2 = client.post("/api/redaction", json=body, headers=hdr(csrf))
    r3 = client.post("/api/redaction", json=body, headers=hdr(csrf))

    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    assert r3.status_code == 429, r3.text
    assert int(r3.headers.get("Retry-After", "0")) >= 1

    s = SessionLocal()
    try:
        rows = s.scalars(
            select(AuditLog).where(AuditLog.event_type == AuditEventType.RATE_LIMITED)
        ).all()
    finally:
        s.close()
    assert rows, "un 429 IA doit laisser une trace d'audit RATE_LIMITED"


def test_ia_rate_limit_desactivable(client, monkeypatch):
    """Drapeau IA_RATE_LIMIT_ENABLED=false -> aucune limitation (429 impossible)."""
    from app.core import rate_limit
    from app.core.config import settings
    from app.services import redaction_service

    monkeypatch.setattr(
        redaction_service,
        "rediger",
        lambda texte, mode, consignes=None: {"texte": "ok", "mode": mode, "model": "test"},
    )
    monkeypatch.setattr(settings, "IA_RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(rate_limit._limiter, "max_per_window", 1)

    csrf = auth(client, "collab")
    body = {"texte": "Texte de test.", "mode": "resume"}
    for _ in range(4):
        r = client.post("/api/redaction", json=body, headers=hdr(csrf))
        assert r.status_code == 200, r.text
