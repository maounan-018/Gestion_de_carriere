#!/usr/bin/env python3
"""
tests/test_reco_cache.py — Cache de la reco « ma-reco ».
Vérifie sans Ollama (recommander monkeypatché) que l'appel répété à profil
inchangé est servi par le cache, et que la signature dépend des entrées.
"""

from app.services import recommendation_service as rs
from app.models.user import User, Role
from app.models.profil import Profil


def test_reco_cache_evite_le_recalcul(db, monkeypatch):
    rs.clear_reco_cache()
    u = User(email="cache@bmci.local", name="Cache Test", role=Role.COLLAB)
    db.add(u)
    db.flush()
    db.add(Profil(user_id=u.id, nom="Test", aspirations="Devenir manager des risques", synthetique=True))
    db.commit()

    calls = {"n": 0}

    def fake_recommander(_db, labels, poste, **kw):
        calls["n"] += 1
        return {"poste_vise": poste, "score_actuel": 42, "plan_developpement": "plan", "labels": labels}

    monkeypatch.setattr(rs, "recommander", fake_recommander)
    # Normalisation d'entrée mockée (passthrough) : pas d'appel Ollama en test.
    monkeypatch.setattr(rs, "normaliser_cible",
                        lambda t: {"intitule": t, "confiance": "clair", "model": "test"})

    r1 = rs.recommander_pour_user(db, u.id)
    r2 = rs.recommander_pour_user(db, u.id)
    assert calls["n"] == 1          # 2e appel servi par le cache (pas de recalcul)
    assert r1 == r2
    rs.clear_reco_cache()


def test_reco_signature_depend_des_entrees():
    a = rs._reco_signature(1, "poste A", ["x", "y"])
    assert a == rs._reco_signature(1, "poste A", ["y", "x"])  # ordre des compétences ignoré
    assert a != rs._reco_signature(1, "poste B", ["x", "y"])  # poste différent -> clé différente
    assert a != rs._reco_signature(2, "poste A", ["x", "y"])  # profil différent -> clé différente
