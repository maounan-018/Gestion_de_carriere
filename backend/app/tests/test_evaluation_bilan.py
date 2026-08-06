#!/usr/bin/env python3
"""
tests/test_evaluation_bilan.py — Journal des bilans d'évaluation (historique).

Quand le manager/RH soumet une évaluation (note globale + appréciation), une ligne
datée est journalisée et RESSORT dans `ProfilOut.evaluations` (le plus récent
d'abord). Ownership : RH/ADMIN ou le manager du profil.
"""

from app.tests.conftest import auth, anon, hdr


def _un_profil(client) -> int:
    auth(client, "rh")
    profils = client.get("/api/profils?limit=5").json()
    assert profils, "aucun profil dans le seed de test"
    return profils[0]["id"]


def test_bilan_apparait_dans_historique(client):
    pid = _un_profil(client)
    csrf = auth(client, "rh")
    r = client.post(f"/api/profils/{pid}/evaluations", headers=hdr(csrf),
                    json={"type": "mission", "note": 4,
                          "commentaire": "Bon trimestre, à confirmer sur le pilotage.",
                          "competences_detectees": 2})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["note"] == 4 and body["competences_detectees"] == 2
    assert body["evaluateur_nom"]  # nom résolu

    # Ressort dans l'historique du profil.
    evals = client.get(f"/api/profils/{pid}").json()["evaluations"]
    assert any(e["id"] == body["id"] and e["note"] == 4 for e in evals)


def test_bilans_journalises_recent_dabord(client):
    pid = _un_profil(client)
    csrf = auth(client, "rh")
    for note in (2, 5):
        client.post(f"/api/profils/{pid}/evaluations", headers=hdr(csrf),
                    json={"type": "mission", "note": note, "commentaire": f"note {note}"})
    evals = client.get(f"/api/profils/{pid}").json()["evaluations"]
    # Journal (pas upsert) : au moins deux lignes, la plus récente en tête.
    assert len(evals) >= 2
    assert evals[0]["note"] == 5


def test_bilan_exige_role_hierarchique(client):
    pid = _un_profil(client)
    csrf = auth(client, "collab")   # un collaborateur ne juge pas autrui
    r = client.post(f"/api/profils/{pid}/evaluations", headers=hdr(csrf),
                    json={"type": "mission", "note": 3})
    assert r.status_code in (403, 404)
    anon(client)
    assert client.post(f"/api/profils/{pid}/evaluations",
                       json={"type": "mission", "note": 3}).status_code in (401, 403)


def test_note_hors_bornes_rejetee(client):
    pid = _un_profil(client)
    csrf = auth(client, "rh")
    assert client.post(f"/api/profils/{pid}/evaluations", headers=hdr(csrf),
                       json={"note": 6}).status_code == 422
