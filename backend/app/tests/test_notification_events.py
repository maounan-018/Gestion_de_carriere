#!/usr/bin/env python3
"""
tests/test_notification_events.py — Notifications émises sur ÉVÈNEMENTS métier.

Prouve, de bout en bout, que les notifications ne sont plus seulement semées mais
émises par les évènements réels :
  - décision de candidature (retenue/refusée) -> notifie le candidat ;
  - souhait poussé -> notifie le manager ;
  - souhait décidé (accordé/refusé) -> notifie le collaborateur.
"""

from app.tests.conftest import auth, hdr


def test_decision_candidature_notifie_le_candidat(client):
    # RH crée une offre ; le collab candidate pour SON profil ; RH décide.
    csrf_rh = auth(client, "rh")
    off = client.post(
        "/api/offres",
        json={"titre": "Analyste Data Notif", "type": "offre_poste"},
        headers=hdr(csrf_rh),
    ).json()["id"]

    csrf_c = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    cand = client.post(
        "/api/candidatures", json={"offre_id": off, "profil_id": mon}, headers=hdr(csrf_c)
    ).json()["id"]

    csrf_rh = auth(client, "rh")
    dec = client.patch(
        f"/api/candidatures/{cand}/decision", json={"statut": "retenue"}, headers=hdr(csrf_rh)
    )
    assert dec.status_code == 200, dec.text

    # Le candidat voit la notification de décision.
    auth(client, "collab")
    notifs = client.get("/api/notifications").json()
    assert any(
        n["titre"] == "Décision sur votre candidature" and "retenue" in (n["texte"] or "")
        for n in notifs
    )


def test_souhait_pousse_notifie_le_manager(client):
    csrf_c = auth(client, "collab")
    client.post(
        "/api/souhaits",
        headers=hdr(csrf_c),
        json={"titre": "[TEST] Vers le management", "pushed": True},
    )

    auth(client, "manager")
    notifs = client.get("/api/notifications").json()
    assert any(
        n["titre"] == "Nouvelle demande d'évolution" and "El Amrani" in (n["texte"] or "")
        for n in notifs
    )


def test_souhait_decide_notifie_le_collaborateur(client):
    # Le collab crée + pousse un souhait…
    csrf_c = auth(client, "collab")
    sid = client.post(
        "/api/souhaits",
        headers=hdr(csrf_c),
        json={"titre": "[TEST] Décision souhait", "pushed": True},
    ).json()["id"]

    # …que la RH accorde -> le collaborateur est notifié.
    csrf_rh = auth(client, "rh")
    r = client.patch(f"/api/souhaits/{sid}", headers=hdr(csrf_rh), json={"statut": "accorde"})
    assert r.status_code == 200, r.text

    auth(client, "collab")
    notifs = client.get("/api/notifications").json()
    assert any(
        n["titre"] == "Réponse à votre demande d'évolution" and "accordé" in (n["texte"] or "")
        for n in notifs
    )
