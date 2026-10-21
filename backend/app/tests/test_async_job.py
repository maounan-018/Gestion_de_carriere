#!/usr/bin/env python3
"""
tests/test_async_job.py — Registre de jobs asynchrones (services/async_job).
Teste le mécanisme (pending→done/error) et l'isolement par propriétaire, sans IA.
"""

import time

from app.services import async_job


def _wait(job_id: int, user_id: int, timeout: float = 3.0) -> dict | None:
    """Attend qu'un job soit terminé (done/error) ou expire."""
    start = time.time()
    while time.time() - start < timeout:
        j = async_job.get(job_id, user_id)
        if j and j["status"] in ("done", "error"):
            return j
        time.sleep(0.02)
    return async_job.get(job_id, user_id)


def test_job_aboutit_avec_resultat():
    job_id = async_job.submit(7, lambda db: {"ok": True}, label="test")
    j = _wait(job_id, 7)
    assert j is not None and j["status"] == "done"
    assert j["result"] == {"ok": True}
    assert j["error"] is None


def test_job_reserve_au_proprietaire():
    job_id = async_job.submit(7, lambda db: 1, label="test")
    assert async_job.get(job_id, 999) is None  # un autre user ne voit pas le job
    assert async_job.get(job_id, 7) is not None
    _wait(job_id, 7)


def test_job_en_erreur_capture_le_message():
    def boom(db):
        raise RuntimeError("panne simulée")

    job_id = async_job.submit(7, boom, label="test")
    j = _wait(job_id, 7)
    assert j is not None and j["status"] == "error"
    assert "panne simulée" in (j["error"] or "")


def test_job_inconnu_renvoie_none():
    assert async_job.get("inexistant", 7) is None
