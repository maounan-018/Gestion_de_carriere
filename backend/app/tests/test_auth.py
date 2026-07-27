#!/usr/bin/env python3
"""
tests/test_auth.py — Authentification locale (login / me / logout).
"""

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


def test_logout_revoque_la_session(client):
    csrf = auth(client, "manager")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout", headers=hdr(csrf)).status_code == 200
    # session révoquée + cookies supprimés -> /me non authentifié
    assert client.get("/api/auth/me").status_code == 401
