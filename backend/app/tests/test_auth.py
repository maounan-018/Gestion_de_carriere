#!/usr/bin/env python3
"""
tests/test_auth.py — Authentification locale (login / me / logout).
"""

from app.core.config import settings
from app.tests.conftest import auth, anon, hdr, ACCOUNTS


def test_login_ok_et_me(client):
    auth(client, "rh")
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == ACCOUNTS["rh"]
    assert me.json()["role"] == "RH"


def test_login_mauvais_mdp_401(client):
    anon(client)
    r = client.post("/api/auth/login", json={"email": ACCOUNTS["rh"], "password": "mauvais"})
    assert r.status_code == 401


def test_login_compte_inexistant_401(client):
    anon(client)
    r = client.post("/api/auth/login", json={"email": "inconnu@bmci.local", "password": "x"})
    assert r.status_code == 401


def test_login_verrouillage_anti_brute_force(client):
    """Anti-brute-force : après MAX_LOGIN_ATTEMPTS échecs récents, le compte est
    verrouillé (429). E-mail dédié (jamais connecté ailleurs) -> pas de contamination."""
    anon(client)
    bad = {"email": "brute-force@bmci.local", "password": "faux"}
    for _ in range(settings.MAX_LOGIN_ATTEMPTS):
        assert client.post("/api/auth/login", json=bad).status_code == 401
    r = client.post("/api/auth/login", json=bad)            # au-delà du seuil
    assert r.status_code == 429
    assert "tentatives" in r.json()["detail"].lower()


def test_logout_revoque_la_session(client):
    csrf = auth(client, "manager")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout", headers=hdr(csrf)).status_code == 200
    # session révoquée + cookies supprimés -> /me non authentifié
    assert client.get("/api/auth/me").status_code == 401
