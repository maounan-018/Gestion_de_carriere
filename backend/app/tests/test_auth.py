#!/usr/bin/env python3
"""
tests/test_auth.py — Authentification locale (login / me / logout).
"""

from app.core.config import settings
from app.tests.conftest import ACCOUNTS, anon, auth, hdr


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
    r = client.post("/api/auth/login", json=bad)  # au-delà du seuil
    assert r.status_code == 429
    assert "tentatives" in r.json()["detail"].lower()


def test_logout_revoque_la_session(client):
    csrf = auth(client, "manager")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout", headers=hdr(csrf)).status_code == 200
    # session révoquée + cookies supprimés -> /me non authentifié
    assert client.get("/api/auth/me").status_code == 401


def test_annuaire_preload_compte_existant(client):
    """Enrôlement : l'e-mail (partie locale) d'un compte pré-existant renvoie ses
    infos RH déjà en base (poste, département, manager) — pré-remplissage, pré-auth."""
    anon(client)
    r = client.get(
        "/api/auth/annuaire-preload", params={"email": "youssef.elamrani@bmci.local"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is True
    assert data["poste_actuel"]  # poste pré-rempli
    assert data["manager_nom"] == "Karim Naji"  # manager résolu depuis la base


def test_annuaire_preload_inconnu_found_false(client):
    anon(client)
    r = client.get(
        "/api/auth/annuaire-preload", params={"email": "personne.inexistante@bmci.local"}
    )
    assert r.status_code == 200
    assert r.json()["found"] is False
