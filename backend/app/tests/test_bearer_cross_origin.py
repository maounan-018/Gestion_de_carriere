#!/usr/bin/env python3
"""
tests/test_bearer_cross_origin.py — Auth CROSS-ORIGIN (déploiement front distant).

Couvre les chemins ajoutés pour un front déployé (ex. Vercel) qui appelle un
backend FastAPI local sur une AUTRE origine :
  - le login renvoie le jeton de session dans le corps (`token`) ;
  - une requête authentifiée par `Authorization: Bearer` SANS cookie fonctionne,
    et le CSRF est sauté (aucun cookie => aucun vecteur CSRF) ;
  - le CSRF reste EXIGÉ pour l'auth par cookie (non-régression) ;
  - le préflight Private Network Access reçoit l'en-tête d'autorisation.
"""

from app.tests.conftest import ACCOUNTS, DEMO_PASSWORD

ORIGIN = "http://localhost:3000"  # présent dans ALLOWED_ORIGINS des tests


def _login(client) -> dict:
    client.cookies.clear()
    r = client.post(
        "/api/auth/login", json={"email": ACCOUNTS["manager"], "password": DEMO_PASSWORD}
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_login_renvoie_le_token_dans_le_corps(client):
    body = _login(client)
    assert isinstance(body.get("token"), str) and body["token"]
    assert isinstance(body.get("csrf_token"), str) and body["csrf_token"]


def test_bearer_sans_cookie_authentifie_et_saute_le_csrf(client):
    """Bearer + AUCUN cookie : /me (GET) marche, et logout (POST mutant) marche
    SANS en-tête CSRF — le double-submit ne s'applique qu'à l'auth par cookie."""
    token = _login(client)["token"]
    client.cookies.clear()  # simule le cross-origin : pas de cookie transmis
    bearer = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=bearer)
    assert me.status_code == 200, me.text
    assert me.json()["email"] == ACCOUNTS["manager"]

    # POST mutant, Bearer, PAS de X-CSRF-Token -> autorisé (pas de 403 CSRF).
    out = client.post("/api/auth/logout", headers=bearer)
    assert out.status_code == 200, out.text


def test_cookie_sans_csrf_reste_refuse(client):
    """Non-régression : en auth par COOKIE, une requête mutante sans CSRF => 403."""
    _login(client)  # cookies (session + csrf) posés sur le client
    r = client.post("/api/auth/logout")  # pas d'en-tête X-CSRF-Token
    assert r.status_code == 403
    assert "csrf" in r.json()["detail"].lower()


def test_preflight_private_network_access(client):
    """Préflight avec Access-Control-Request-Private-Network: true => le backend
    répond Access-Control-Allow-Private-Network: true (site public -> localhost)."""
    r = client.options(
        "/api/auth/login",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Private-Network": "true",
        },
    )
    assert r.headers.get("access-control-allow-origin") == ORIGIN
    assert r.headers.get("access-control-allow-private-network") == "true"


def test_preflight_sans_pna_nomet_pas_len_tete(client):
    """Sans l'en-tête de requête PNA, l'en-tête d'autorisation n'est PAS posé."""
    r = client.options(
        "/api/auth/login",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-private-network" not in r.headers
