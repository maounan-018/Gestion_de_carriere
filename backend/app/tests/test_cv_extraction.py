#!/usr/bin/env python3
"""
tests/test_cv_extraction.py — Extraction CV → profil (compétences détenues).

Unitaire (ancrage + niveau) et e2e (enrichit le profil du propriétaire, interdit
sur le profil d'autrui, ré-extraction idempotente). L'IA est monkeypatchée : pas
d'appel Ollama pendant les tests.
"""

from app.tests.conftest import auth, hdr

_MATCH = [
    {
        "skill_id": 42,
        "label_fr": "Analyse des risques de crédit",
        "label_en": "x",
        "skill_type": "skill",
        "distance": 0.1,
        "score": 0.9,
    }
]


def test_extraire_cv_ancre_et_niveau(db, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(
        cv,
        "generate",
        lambda task, prompt, system="", is_valid=None: {
            "competences": [
                {"libelle": "Analyse de crédit", "type": "savoir-faire", "niveau": 4},
                {
                    "libelle": "Python",
                    "type": "savoir-faire",
                    "niveau": 9,
                },  # niveau hors bornes -> None
                {"libelle": "   ", "type": "savoir"},  # vide -> ignoré
            ]
        },
    )
    monkeypatch.setattr(cv, "search_skills", lambda db, libelle, k=1: _MATCH)

    out = cv.extraire_cv(db, "CV avec analyse de crédit et python", top_k=1)
    assert len(out) == 2  # le libellé vide est ignoré
    assert out[0]["skill_id"] == 42 and out[0]["niveau"] == 4
    assert out[1]["niveau"] is None  # 9 rejeté (hors 1-5)


def test_cv_extraction_enrichit_profil_owner(client, monkeypatch):
    from app.database.session import SessionLocal
    from app.models.skill import Skill
    from app.services import cv_extraction_service as cv

    # L'ancrage persistera `skill_id` dans `profil_competences` : avec FK ON (session.py),
    # ce `skill_id` DOIT exister dans `skills`. On en crée un dédié au test au lieu
    # d'un id hard-codé (le seed de `client` ne charge pas le graphe ESCO complet).
    with SessionLocal() as s:
        skill = Skill(
            label_fr="Gestion des risques (test)",
            label_en="Risk management (test)",
            skill_type="skill",
        )
        s.add(skill)
        s.commit()
        skill_id = skill.id
    monkeypatch.setattr(
        cv,
        "generate",
        lambda *a, **k: {
            "competences": [{"libelle": "Gestion du risque", "type": "savoir-faire", "niveau": 3}]
        },
    )
    monkeypatch.setattr(
        cv,
        "search_skills",
        lambda db, libelle, k=1: [
            {
                "skill_id": skill_id,
                "label_fr": "Gestion des risques",
                "label_en": "x",
                "skill_type": "skill",
                "distance": 0.2,
                "score": 0.8,
            }
        ],
    )

    csrf = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    r = client.post(
        f"/api/profils/{mon}/extraction-cv",
        headers=hdr(csrf),
        json={"texte": "CV : 10 ans en gestion des risques bancaires."},
    )
    assert r.status_code == 200, r.text
    cv_comps = [c for c in r.json()["competences"] if c["source"] == "cv"]
    assert any(
        c["libelle"] == "Gestion du risque" and c["skill_id"] == skill_id and c["niveau"] == 3
        for c in cv_comps
    )


def test_cv_extraction_interdite_sur_profil_autrui(client, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(
        cv, "generate", lambda *a, **k: {"competences": [{"libelle": "X", "type": "savoir"}]}
    )
    monkeypatch.setattr(cv, "search_skills", lambda *a, **k: [])

    auth(client, "rh")
    autre = next(p["id"] for p in client.get("/api/profils").json() if p["nom"] != "El Amrani")
    csrf = auth(client, "collab")
    r = client.post(
        f"/api/profils/{autre}/extraction-cv",
        headers=hdr(csrf),
        json={"texte": "un CV quelconque pour autrui"},
    )
    assert r.status_code == 403


def test_cv_extraction_remplace_idempotent(client, monkeypatch):
    from app.services import cv_extraction_service as cv

    monkeypatch.setattr(
        cv,
        "generate",
        lambda *a, **k: {
            "competences": [
                {"libelle": "Conformité réglementaire", "type": "savoir", "niveau": None}
            ]
        },
    )
    monkeypatch.setattr(cv, "search_skills", lambda *a, **k: [])

    csrf = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    body = {"texte": "CV conformité réglementaire bancaire.", "remplacer": True}
    client.post(f"/api/profils/{mon}/extraction-cv", headers=hdr(csrf), json=body)
    r = client.post(f"/api/profils/{mon}/extraction-cv", headers=hdr(csrf), json=body)
    cv_comps = [
        c
        for c in r.json()["competences"]
        if c["source"] == "cv" and c["libelle"] == "Conformité réglementaire"
    ]
    assert len(cv_comps) == 1  # remplacé, pas dupliqué
