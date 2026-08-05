#!/usr/bin/env python3
"""
tests/test_front_endpoints.py — Endpoints alimentant le front (Batch 1) :
notifications, souhaits (+ /recus), formations. Couvre auth, RBAC et ownership.
"""

from app.tests.conftest import auth, anon, hdr


# ------------------------------------------------------------- Formations
def test_formations_liste_et_filtre(client):
    auth(client, "collab")
    r = client.get("/api/formations")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 10
    assert isinstance(data[0]["tags"], list)  # CSV -> liste

    r = client.get("/api/formations", params={"domaine": "Management"})
    assert r.status_code == 200
    assert r.json() and all(f["domaine"] == "Management" for f in r.json())


def test_formations_exige_auth(client):
    anon(client)
    assert client.get("/api/formations").status_code == 401


# ----------------------------------------------------------- Notifications
def test_notifications_du_collaborateur(client):
    auth(client, "collab")
    r = client.get("/api/notifications")
    assert r.status_code == 200
    notifs = r.json()
    assert len(notifs) >= 3
    assert {"id", "type", "titre", "lu", "to_route"} <= set(notifs[0])


def test_notification_marquer_lue(client):
    csrf = auth(client, "collab")
    nid = client.get("/api/notifications").json()[0]["id"]
    r = client.patch(f"/api/notifications/{nid}/lu", headers=hdr(csrf))
    assert r.status_code == 200 and r.json()["lu"] is True


def test_notifications_exige_auth(client):
    anon(client)
    assert client.get("/api/notifications").status_code == 401


# --------------------------------------------------------------- Souhaits
def test_souhaits_collaborateur_crud(client):
    csrf = auth(client, "collab")
    assert len(client.get("/api/souhaits").json()) >= 2  # 2 semés

    r = client.post("/api/souhaits", headers=hdr(csrf),
                    json={"titre": "[TEST] Mobilité data", "kind": "carriere", "horizon": "1 an"})
    assert r.status_code == 201
    sid = r.json()["id"]
    assert r.json()["statut"] == "brouillon" and r.json()["pushed"] is False

    r = client.patch(f"/api/souhaits/{sid}", headers=hdr(csrf), json={"pushed": True})
    assert r.status_code == 200
    assert r.json()["pushed"] is True and r.json()["statut"] == "pousse"


def test_souhaits_recus_interdit_au_collab(client):
    auth(client, "collab")
    assert client.get("/api/souhaits/recus").status_code == 403


def test_souhaits_recus_manager_voit_son_equipe(client):
    # Youssef pousse un souhait…
    csrf = auth(client, "collab")
    client.post("/api/souhaits", headers=hdr(csrf),
                json={"titre": "[TEST] Poussé au manager", "pushed": True})
    # …que son manager Karim doit voir, avec l'identité du membre.
    auth(client, "manager")
    r = client.get("/api/souhaits/recus")
    assert r.status_code == 200
    recus = r.json()
    assert recus and any(s.get("membre_nom") == "El Amrani" for s in recus)
