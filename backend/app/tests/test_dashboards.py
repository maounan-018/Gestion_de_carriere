#!/usr/bin/env python3
"""
tests/test_dashboards.py — Tableaux de bord & agrégations (Batch 2) :
KPIs (RH/manager), cartographie, hauts potentiels. Couvre RBAC.
"""

from app.tests.conftest import auth, anon


def test_kpis_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/kpis", params={"scope": "rh"})
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "rh"
    keys = {k["key"] for k in body["kpis"]}
    # « Offres publiées » et « Candidatures » sont scopées au compte HRBP et
    # mènent à une liste (rh_offres / rh_candidatures), plus à l'écran offres internes.
    assert {"effectif", "rh_offres", "rh_candidatures", "competences"} <= keys


def test_kpis_manager(client):
    auth(client, "manager")
    r = client.get("/api/dashboards/kpis", params={"scope": "manager"})
    assert r.status_code == 200
    assert r.json()["scope"] == "manager"
    assert {"equipe", "offres", "souhaits"} <= {k["key"] for k in r.json()["kpis"]}


def test_kpis_rh_interdit_au_collab(client):
    auth(client, "collab")
    assert client.get("/api/dashboards/kpis", params={"scope": "rh"}).status_code == 403


def test_cartographie_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/cartographie")
    assert r.status_code == 200
    data = r.json()
    # Matrice data-driven : familles (colonnes) + lignes (pôles), niveaux alignés.
    assert {"familles", "lignes"} <= set(data)
    assert isinstance(data["familles"], list)
    if data["lignes"]:
        ligne = data["lignes"][0]
        assert {"departement_key", "label", "effectif", "niveaux"} <= set(ligne)
        # `niveaux` est aligné sur `familles` (une cellule par colonne).
        assert len(ligne["niveaux"]) == len(data["familles"])


def test_cartographie_interdite_au_collab(client):
    auth(client, "collab")
    assert client.get("/api/dashboards/cartographie").status_code == 403


def test_hauts_potentiels_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/hauts-potentiels")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert 0 <= data[0]["score"] <= 100
        assert data[0]["nb_competences"] >= 2


def test_dashboards_exige_auth(client):
    anon(client)
    assert client.get("/api/dashboards/cartographie").status_code == 401
