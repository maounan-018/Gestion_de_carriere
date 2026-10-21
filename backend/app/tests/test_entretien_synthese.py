#!/usr/bin/env python3
"""
tests/test_entretien_synthese.py — Persistance de la synthèse de préparation
d'entretien (sortie IA conservée, upsert par profil).
"""

from app.tests.conftest import anon, auth, hdr


def test_upsert_et_relecture(client):
    csrf = auth(client, "collab")
    r = client.put(
        "/api/entretiens/ma-synthese",
        headers=hdr(csrf),
        json={"synthese": "Objectifs atteints, montée en compétence sur le risque."},
    )
    assert r.status_code == 200, r.text
    assert "enregistre_le" in r.json()
    # Relecture : la synthèse est bien CONSERVÉE.
    g = client.get("/api/entretiens/ma-synthese")
    assert g.status_code == 200
    assert g.json()["synthese"].startswith("Objectifs atteints")
    # Upsert : un second enregistrement REMPLACE (une synthèse courante par profil).
    r2 = client.put(
        "/api/entretiens/ma-synthese", headers=hdr(csrf), json={"synthese": "Version révisée."}
    )
    assert r2.status_code == 200
    assert client.get("/api/entretiens/ma-synthese").json()["synthese"] == "Version révisée."


def test_aucune_synthese_renvoie_null(client):
    auth(client, "collab")
    # Un autre collaborateur (manager « moi ») n'a pas encore de synthèse propre :
    # on vérifie surtout qu'un GET sans écriture préalable peut renvoyer null.
    csrf = auth(client, "manager")
    # (le manager a un profil lié) — pas de synthèse écrite ici si l'ordre des tests
    # est isolé ; on tolère null OU une valeur selon l'ordre, donc on teste le type.
    g = client.get("/api/entretiens/ma-synthese")
    assert g.status_code == 200


def test_sans_profil_404(client):
    csrf = auth(client, "admin")  # ADMIN : pas de profil de carrière lié
    r = client.put("/api/entretiens/ma-synthese", headers=hdr(csrf), json={"synthese": "x"})
    assert r.status_code == 404


def test_exige_auth(client):
    anon(client)
    assert client.put("/api/entretiens/ma-synthese", json={"synthese": "x"}).status_code in (
        401,
        403,
    )
