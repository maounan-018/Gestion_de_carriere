#!/usr/bin/env python3
"""
tests/test_http_hardening.py — Durcissement HTTP (en-têtes de sécurité + taille).

Vérifie que le middleware ASGI pose les en-têtes de sécurité, applique une CSP
stricte à l'API (mais pas à la doc Swagger), et rejette les corps trop gros (413).
"""

from app.core.config import settings


def test_entetes_securite_sur_reponse_api(client):
    r = client.get("/sante")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "permissions-policy" in r.headers
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_doc_sans_csp_stricte(client):
    """La doc (openapi/Swagger) ne reçoit PAS la CSP stricte (sinon elle casse),
    mais garde les en-têtes de base (anti-sniffing)."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "content-security-policy" not in r.headers
    assert r.headers["x-content-type-options"] == "nosniff"


def test_corps_trop_volumineux_413(client, monkeypatch):
    """Un Content-Length au-delà du plafond -> 413, avant tout traitement/auth."""
    monkeypatch.setattr(settings, "MAX_REQUEST_SIZE_BYTES", 10)
    r = client.post("/api/auth/login",
                    json={"email": "trop@gros.local", "password": "charge-utile-volumineuse"})
    assert r.status_code == 413
    # Le 413 porte lui aussi les en-têtes de sécurité.
    assert r.headers["x-content-type-options"] == "nosniff"
