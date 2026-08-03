#!/usr/bin/env python3
"""tests/test_message_rh.py — Manager → RH : POST /api/notifications/message-rh."""

from app.tests.conftest import auth, hdr


def test_message_rh_cree_des_notifications(client):
    csrf = auth(client, "manager")
    r = client.post("/api/notifications/message-rh",
                    json={"sujet": "Renfort Retail", "message": "Besoin d'un profil senior."},
                    headers=hdr(csrf))
    assert r.status_code == 200, r.text
    assert r.json()["destinataires"] >= 1          # au moins Nadia (RH)


def test_message_rh_interdit_au_collab(client):
    csrf = auth(client, "collab")
    r = client.post("/api/notifications/message-rh",
                    json={"message": "coucou"}, headers=hdr(csrf))
    assert r.status_code == 403
