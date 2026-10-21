#!/usr/bin/env python3
"""
tests/test_evaluation_extraction.py — Extraction depuis une ÉVALUATION → profil.

Compétences DÉMONTRÉES extraites d'une évaluation de mission/performance, ajoutées
au profil avec la source correspondante. Ownership : RH/ADMIN ou le MANAGER du
profil (jamais l'auto-déclaration). IA monkeypatchée (pas d'Ollama).
"""

from app.tests.conftest import auth, hdr


def _fake_comps(*a, **k):
    return [
        {
            "libelle": "Leadership",
            "categorie": "savoir-être",
            "niveau": 4,
            "skill_id": None,
            "skill_label_fr": None,
        }
    ]


def test_extraire_evaluation_service_utilise_le_bon_prompt(db, monkeypatch):
    from app.services import cv_extraction_service as cv

    cap = {}

    def fake_generate(task, prompt, system="", is_valid=None):
        cap["system"] = system
        return {"competences": [{"libelle": "Rigueur", "type": "savoir-être", "niveau": 3}]}

    monkeypatch.setattr(cv, "generate", fake_generate)
    monkeypatch.setattr(cv, "search_skills", lambda *a, **k: [])
    out = cv.extraire_evaluation(db, "compte-rendu d'évaluation de mission", top_k=1)
    assert out and out[0]["libelle"] == "Rigueur" and out[0]["niveau"] == 3
    assert "ÉVALUATION" in cap["system"]  # prompt évaluation (pas CV)


def test_manager_extrait_evaluation_de_son_equipe(client, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(cv, "extraire_evaluation", _fake_comps)

    auth(client, "rh")
    bennani = next(p["id"] for p in client.get("/api/profils").json() if p["nom"] == "El Amrani")
    csrf = auth(client, "manager")
    r = client.post(
        f"/api/profils/{bennani}/extraction-evaluation",
        headers=hdr(csrf),
        json={"texte": "Évaluation de mission : excellent leadership démontré.", "type": "mission"},
    )
    assert r.status_code == 200, r.text
    assert any(
        c["source"] == "evaluation_mission" and c["libelle"] == "Leadership"
        for c in r.json()["competences"]
    )


def test_collab_ne_sauto_evalue_pas(client, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(cv, "extraire_evaluation", _fake_comps)

    csrf = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    r = client.post(
        f"/api/profils/{mon}/extraction-evaluation",
        headers=hdr(csrf),
        json={"texte": "Auto-évaluation : je suis excellent.", "type": "mission"},
    )
    assert r.status_code == 403


def test_rh_extrait_evaluation_performance(client, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(cv, "extraire_evaluation", _fake_comps)

    csrf = auth(client, "rh")
    pid = client.post(
        "/api/profils", json={"nom": "EvalPerf", "synthetique": True}, headers=hdr(csrf)
    ).json()["id"]
    r = client.post(
        f"/api/profils/{pid}/extraction-evaluation",
        headers=hdr(csrf),
        json={
            "texte": "Évaluation annuelle de performance du collaborateur.",
            "type": "performance",
        },
    )
    assert r.status_code == 200, r.text
    assert any(c["source"] == "evaluation_performance" for c in r.json()["competences"])
