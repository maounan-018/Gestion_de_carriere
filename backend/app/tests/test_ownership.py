#!/usr/bin/env python3
"""
tests/test_ownership.py — Ownership ligne-à-ligne (B2), de bout en bout.

Prouve le cloisonnement par PÉRIMÈTRE (au-delà du RBAC) sur profils & candidatures :
  - COLLAB  : SON profil / SES candidatures uniquement ;
  - MANAGER : lui + SON ÉQUIPE (le collab Bennani est managé par le manager) ;
  - RH/ADMIN : global.
Les ids « hors périmètre » sont des personas synthétiques (user_id NULL), invisibles
aux managers. Découverte des ids faite en tant que RH (périmètre global).
"""

from app.tests.conftest import auth, hdr


# ------------------------------------------------------------------ Profils

def test_collab_lit_son_profil_pas_celui_dautrui(client):
    auth(client, "rh")
    profils = client.get("/api/profils").json()
    autre = next(p["id"] for p in profils if p["nom"] != "Bennani")  # pas le profil du collab

    auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    assert client.get(f"/api/profils/{mon}").status_code == 200            # son profil
    assert client.get(f"/api/profils/{autre}/carriere").status_code == 403  # profil d'autrui


def test_manager_lit_equipe_pas_hors_equipe(client):
    csrf = auth(client, "rh")
    profils = client.get("/api/profils").json()
    bennani = next(p["id"] for p in profils if p["nom"] == "Bennani")       # équipe du manager
    synth = client.post("/api/profils", json={"nom": "HorsEquipe", "synthetique": True},
                        headers=hdr(csrf)).json()["id"]                      # persona hors équipe

    auth(client, "manager")
    assert client.get(f"/api/profils/{bennani}/carriere").status_code == 200
    assert client.get(f"/api/profils/{synth}/carriere").status_code == 403


def test_liste_profils_manager_bornee_a_son_equipe(client):
    csrf = auth(client, "rh")
    synth = client.post("/api/profils", json={"nom": "HorsEquipe2", "synthetique": True},
                        headers=hdr(csrf)).json()["id"]

    auth(client, "manager")
    profils = client.get("/api/profils").json()   # sans manager_id : périmètre forcé à SON équipe
    ids = {p["id"] for p in profils}
    assert synth not in ids                        # persona hors équipe absent
    assert any(p["nom"] == "Bennani" for p in profils)


# --------------------------------------------------------------- Candidatures

def test_collab_liste_candidatures_bornee(client):
    auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    assert client.get("/api/candidatures").status_code == 403                      # sans filtre -> refus
    assert client.get("/api/candidatures", params={"profil_id": mon}).status_code == 200
    assert client.get("/api/candidatures", params={"profil_id": 999999}).status_code == 403


def test_collab_ne_lit_pas_candidature_dautrui(client):
    # RH crée une offre + une candidature pour un profil synthétique (pas le collab).
    csrf = auth(client, "rh")
    off = client.post("/api/offres", json={"titre": "Poste Own", "type": "offre_poste"},
                      headers=hdr(csrf)).json()["id"]
    synth = client.post("/api/profils", json={"nom": "CandOwn", "synthetique": True},
                        headers=hdr(csrf)).json()["id"]
    cand = client.post("/api/candidatures", json={"offre_id": off, "profil_id": synth},
                       headers=hdr(csrf)).json()["id"]

    assert client.get(f"/api/candidatures/{cand}").status_code == 200   # RH : global
    auth(client, "collab")
    assert client.get(f"/api/candidatures/{cand}").status_code == 403   # pas sa candidature
