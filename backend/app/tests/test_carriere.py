#!/usr/bin/env python3
"""
tests/test_carriere.py — Profil carrière enrichi + filtre équipe (Batch 3).
"""

from app.tests.conftest import anon, auth


def _profil_id(client, nom: str) -> int:
    profils = client.get("/api/profils").json()
    return next(p["id"] for p in profils if p["nom"] == nom)


def test_carriere_profil(client):
    auth(client, "rh")
    pid = _profil_id(client, "El Amrani")
    r = client.get(f"/api/profils/{pid}/carriere")
    assert r.status_code == 200
    body = r.json()
    assert body["profil_id"] == pid
    assert body["stations"] and body["avis_pairs"]
    assert any(s["etat"] == "objectif" for s in body["stations"])
    assert {"periode", "titre", "etat"} <= set(body["stations"][0])
    assert {"auteur_nom", "texte", "etoiles"} <= set(body["avis_pairs"][0])


def test_carriere_404(client):
    auth(client, "rh")
    assert client.get("/api/profils/999999/carriere").status_code == 404


def test_carriere_exige_auth(client):
    anon(client)
    assert client.get("/api/profils/1/carriere").status_code == 401


def test_liste_profils_filtre_equipe(client):
    auth(client, "manager")
    me = client.get("/api/auth/me").json()
    r = client.get("/api/profils", params={"manager_id": me["id"]})
    assert r.status_code == 200
    # Youssef El Amrani est managé par Karim -> présent dans son équipe.
    assert any(p["nom"] == "El Amrani" for p in r.json())
