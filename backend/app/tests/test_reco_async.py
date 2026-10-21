#!/usr/bin/env python3
"""
tests/test_reco_async.py — Job asynchrone de reco (lancement + polling + ownership).
Teste le MÉCANISME (thread + job store) sans Ollama : `recommander_pour_user` est
monkeypatché pour renvoyer instantanément.
"""

import time

from app.services import recommendation_service as rs


def _wait_done(job_id: str, user_id: int, tries: int = 80) -> dict | None:
    for _ in range(tries):
        j = rs.get_reco_job(job_id, user_id)
        if j and j["status"] in ("done", "error"):
            return j
        time.sleep(0.05)
    return rs.get_reco_job(job_id, user_id)


def test_job_lance_et_se_termine(monkeypatch):
    monkeypatch.setattr(
        rs, "recommander_pour_user", lambda _db, _uid: {"poste_vise": "Manager", "score_actuel": 50}
    )
    job_id = rs.launch_reco_job(user_id=77)
    assert isinstance(job_id, str) and job_id
    # Immédiatement après le lancement, le job existe (pending ou déjà done).
    assert rs.get_reco_job(job_id, 77) is not None
    j = _wait_done(job_id, 77)
    assert j and j["status"] == "done"
    assert j["result"]["poste_vise"] == "Manager"


def test_job_ownership(monkeypatch):
    monkeypatch.setattr(rs, "recommander_pour_user", lambda _db, _uid: {"ok": True})
    job_id = rs.launch_reco_job(user_id=5)
    assert rs.get_reco_job(job_id, 6) is None  # autre utilisateur -> aucun accès
    assert rs.get_reco_job("inexistant", 5) is None  # job inconnu


def test_job_capte_les_erreurs(monkeypatch):
    def boom(_db, _uid):
        raise RuntimeError("Ollama indisponible")

    monkeypatch.setattr(rs, "recommander_pour_user", boom)
    j = _wait_done(rs.launch_reco_job(user_id=9), 9)
    assert j and j["status"] == "error" and "Ollama" in (j["error"] or "")
