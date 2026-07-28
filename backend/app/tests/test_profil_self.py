#!/usr/bin/env python3
"""
tests/test_profil_self.py — Auto-édition du profil par le collaborateur
(PATCH /api/profils/me) : champs self-safe uniquement, ownership implicite.
"""

from app.tests.conftest import auth, anon, hdr


def test_self_edit_ok(client):
    csrf = auth(client, "collab")
    r = client.patch("/api/profils/me", headers=hdr(csrf),
                     json={"aspirations": "Devenir Directeur Régional"})
    assert r.status_code == 200
    assert r.json()["aspirations"] == "Devenir Directeur Régional"


def test_self_edit_ignore_champs_org(client):
    """Un champ d'organisation (departement_key) n'est pas dans ProfilSelfUpdate
    → ignoré par Pydantic : impossible de se réaffecter un département."""
    csrf = auth(client, "collab")
    r = client.patch("/api/profils/me", headers=hdr(csrf),
                     json={"poste_actuel": "Conseiller senior", "departement_key": "HACK"})
    assert r.status_code == 200
    assert r.json()["poste_actuel"] == "Conseiller senior"
    assert r.json()["departement_key"] != "HACK"


def test_self_edit_sans_profil_404(client):
    """L'ADMIN n'a pas de profil de carrière lié → 404 (rien à éditer)."""
    csrf = auth(client, "admin")
    r = client.patch("/api/profils/me", headers=hdr(csrf), json={"aspirations": "x"})
    assert r.status_code == 404


def test_self_edit_exige_auth(client):
    anon(client)
    assert client.patch("/api/profils/me", json={"aspirations": "x"}).status_code in (401, 403)
