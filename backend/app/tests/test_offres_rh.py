#!/usr/bin/env python3
"""
tests/test_offres_rh.py — Offres côté RH : liste avec stats + candidats (revue).
Couvre le RBAC (RH/ADMIN, MANAGER pour les candidats ; collab interdit).
"""

from app.tests.conftest import anon, auth


def test_rh_liste_offres(client):
    auth(client, "rh")
    r = client.get("/api/offres/rh-liste")
    assert r.status_code == 200
    assert isinstance(r.json(), list)  # peut être vide (base de test sans fiches)


def test_rh_liste_interdite_au_collab(client):
    auth(client, "collab")
    assert client.get("/api/offres/rh-liste").status_code == 403


def test_candidats_offre_rbac(client):
    auth(client, "rh")
    assert client.get("/api/offres/1/candidats").status_code == 200  # liste (vide si pas d'offre)
    auth(client, "collab")
    assert client.get("/api/offres/1/candidats").status_code == 403


def test_rh_liste_exige_auth(client):
    anon(client)
    assert client.get("/api/offres/rh-liste").status_code == 401
