#!/usr/bin/env python3
"""
tests/test_formation_generation.py — Génération de formations synthétiques (LMS).

Service (ancrage + repli) + endpoint (RBAC RH/ADMIN, persistance au catalogue).
IA monkeypatchée : pas d'appel Ollama.
"""

from app.tests.conftest import auth, hdr


def test_generer_formation_ancre_et_structure(db, monkeypatch):
    from app.services import formation_generation_service as fg
    monkeypatch.setattr(fg, "search_skills", lambda db, q, k=1: [{"label_fr": "Analyse du risque de crédit"}])
    monkeypatch.setattr(fg, "generate", lambda task, prompt, system="", is_valid=None: {
        "titre": "Maîtriser le risque de crédit", "organisme": "Académie X", "duree": "14 h",
        "niveau": "Intermédiaire", "domaine": "Risques",
        "objectifs": ["Comprendre le scoring", "Appliquer IFRS 9"],
        "modules": ["Bases", "Scoring", "Provisionnement"], "tags": ["risque", "crédit"]})

    out = fg.generer(db, "risque credit")
    assert out["titre"] == "Maîtriser le risque de crédit"
    assert out["skill_cible"] == "Analyse du risque de crédit"   # ancré sur le référentiel
    assert out["modules"] == ["Bases", "Scoring", "Provisionnement"]
    assert out["synthetique"] is True


def test_generer_formation_repli_si_ia_ko(db, monkeypatch):
    from app.services import formation_generation_service as fg
    monkeypatch.setattr(fg, "search_skills", lambda *a, **k: [])

    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(fg, "generate", boom)
    out = fg.generer(db, "Conformité réglementaire")
    assert out["synthetique"] is True
    assert "Conformité réglementaire" in out["titre"]            # repli fondé sur la saisie


def test_generer_formation_interdit_au_collab(client, monkeypatch):
    from app.services import formation_generation_service as fg
    monkeypatch.setattr(fg, "search_skills", lambda *a, **k: [])
    monkeypatch.setattr(fg, "generate", lambda *a, **k: {"titre": "T", "modules": ["m"]})
    csrf = auth(client, "collab")
    r = client.post("/api/formations/generer", json={"competence": "python"}, headers=hdr(csrf))
    assert r.status_code == 403


def test_generer_formation_rh_persiste_au_catalogue(client, monkeypatch):
    from app.services import formation_generation_service as fg
    monkeypatch.setattr(fg, "search_skills", lambda *a, **k: [])
    monkeypatch.setattr(fg, "generate", lambda *a, **k: {
        "titre": "[TEST] Formation générée", "organisme": "Y", "modules": ["m1"],
        "objectifs": ["o"], "tags": ["t"]})

    csrf = auth(client, "rh")
    avant = len(client.get("/api/formations").json())
    r = client.post("/api/formations/generer",
                    json={"competence": "conformite", "persister": True}, headers=hdr(csrf))
    assert r.status_code == 200, r.text
    assert r.json()["id"] is not None and r.json()["synthetique"] is True
    apres = len(client.get("/api/formations").json())
    assert apres == avant + 1
