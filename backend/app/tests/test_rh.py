#!/usr/bin/env python3
"""
tests/test_rh.py — Veille des entretiens & alertes RH (Batch 4).
"""

from app.tests.conftest import auth, anon


def test_veille(client):
    auth(client, "rh")
    r = client.get("/api/rh/veille")
    assert r.status_code == 200
    data = r.json()
    assert {v["key"] for v in data} == {"annuels", "rh"}
    assert all({"realises", "planifies", "en_retard"} <= set(v) for v in data)


def test_alertes(client):
    auth(client, "rh")
    r = client.get("/api/rh/alertes")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert {"kind", "severity", "titre", "cta"} <= set(data[0])


def test_rh_interdit_au_collab(client):
    auth(client, "collab")
    assert client.get("/api/rh/veille").status_code == 403
    assert client.get("/api/rh/alertes").status_code == 403


def test_rh_exige_auth(client):
    anon(client)
    assert client.get("/api/rh/veille").status_code == 401
