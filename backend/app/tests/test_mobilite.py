#!/usr/bin/env python3
"""
tests/test_mobilite.py — Passerelles de mobilité d'un profil.

Ownership (propriétaire / manager d'équipe / RH) + plomberie (skill_ids détenus
passés au moteur de passerelles). `suggest_occupations` est monkeypatché (pas de
dépendance au graphe réel pendant le test).
"""

from app.tests.conftest import auth


def test_mobilite_owner(client, monkeypatch):
    from app.services import occupation_service
    cap = {}

    def fake(db, skill_ids, k=5, min_shared=2, exclude_labels=None):
        cap["skill_ids"] = skill_ids
        cap["exclude"] = exclude_labels
        return [{"occupation_id": 1, "metier": "Analyste risques", "source": "esco",
                 "competences_partagees": 3}]

    monkeypatch.setattr(occupation_service, "suggest_occupations", fake)
    auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    r = client.get(f"/api/profils/{mon}/mobilite")
    assert r.status_code == 200
    assert r.json()[0]["metier"] == "Analyste risques"
    assert "skill_ids" in cap                       # le moteur a bien reçu les compétences détenues


def test_mobilite_manager_voit_son_equipe(client, monkeypatch):
    from app.services import occupation_service
    monkeypatch.setattr(occupation_service, "suggest_occupations",
                        lambda *a, **k: [{"occupation_id": 2, "metier": "Chef de projet",
                                          "source": "esco", "competences_partagees": 4}])
    auth(client, "rh")
    bennani = next(p["id"] for p in client.get("/api/profils").json() if p["nom"] == "El Amrani")
    auth(client, "manager")
    assert client.get(f"/api/profils/{bennani}/mobilite").status_code == 200


def test_mobilite_interdite_sur_profil_autrui(client, monkeypatch):
    from app.services import occupation_service
    monkeypatch.setattr(occupation_service, "suggest_occupations", lambda *a, **k: [])
    auth(client, "rh")
    autre = next(p["id"] for p in client.get("/api/profils").json() if p["nom"] != "El Amrani")
    auth(client, "collab")
    assert client.get(f"/api/profils/{autre}/mobilite").status_code == 403
