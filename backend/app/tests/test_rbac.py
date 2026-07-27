#!/usr/bin/env python3
"""
tests/test_rbac.py — Preuve de la matrice RBAC (Bloc C) de bout en bout.

Vérifie, via l'API réelle (auth locale + cookies + CSRF) :
  - anonyme : GET protégé -> 401, mutation -> 403 (CSRF) ;
  - mauvais rôle -> 403 ; bon rôle -> 2xx ;
  - règle type↔rôle sur les offres ;
  - CSRF obligatoire sur les mutations ;
  - identité côté serveur : `decided_by` = session (non usurpable).
"""

from app.tests.conftest import auth, anon, hdr


# ---- 1. Anonyme : aucun accès -------------------------------------------------
def test_anon_get_protege_401(client):
    anon(client)
    assert client.get("/api/profils").status_code == 401
    assert client.get("/api/offres").status_code == 401
    assert client.get("/api/candidatures").status_code == 401
    assert client.get("/api/fiches/gabarit").status_code == 401


def test_anon_mutation_bloquee_403(client):
    anon(client)
    # POST sans session : le CSRF échoue avant l'auth -> 403 (bloqué)
    assert client.post("/api/offres", json={"titre": "X", "type": "offre_poste"}).status_code == 403
    assert client.post("/api/profils", json={"nom": "X"}).status_code == 403


# ---- 2. Mauvais rôle : 403 ----------------------------------------------------
def test_collab_ne_cree_pas_offre(client):
    csrf = auth(client, "collab")
    assert client.post("/api/offres", json={"titre": "X", "type": "mission"},
                       headers=hdr(csrf)).status_code == 403


def test_collab_ne_cree_pas_profil(client):
    csrf = auth(client, "collab")
    assert client.post("/api/profils", json={"nom": "X"}, headers=hdr(csrf)).status_code == 403


def test_collab_ne_decide_pas(client):
    csrf = auth(client, "collab")
    assert client.patch("/api/candidatures/1/decision", json={"statut": "retenue"},
                        headers=hdr(csrf)).status_code == 403


def test_manager_ne_cree_pas_profil(client):
    csrf = auth(client, "manager")
    assert client.post("/api/profils", json={"nom": "X"}, headers=hdr(csrf)).status_code == 403


def test_collab_ne_genere_pas_fiche(client):
    csrf = auth(client, "collab")
    assert client.post("/api/fiches/generation", json={"departement_key": "retail_banking",
                       "metier": "X"}, headers=hdr(csrf)).status_code == 403


# ---- 3. Règle type ↔ rôle (offres) --------------------------------------------
def test_rh_ne_pousse_que_offre_poste(client):
    csrf = auth(client, "rh")
    assert client.post("/api/offres", json={"titre": "Mission X", "type": "mission"},
                       headers=hdr(csrf)).status_code == 403
    assert client.post("/api/offres", json={"titre": "Poste X", "type": "offre_poste"},
                       headers=hdr(csrf)).status_code == 201


def test_manager_ne_pousse_pas_offre_poste(client):
    csrf = auth(client, "manager")
    assert client.post("/api/offres", json={"titre": "Poste Y", "type": "offre_poste"},
                       headers=hdr(csrf)).status_code == 403
    assert client.post("/api/offres", json={"titre": "Mission Y", "type": "mission"},
                       headers=hdr(csrf)).status_code == 201


# ---- 4. Bon rôle : 2xx --------------------------------------------------------
def test_rh_cree_profil(client):
    csrf = auth(client, "rh")
    assert client.post("/api/profils", json={"nom": "Test", "synthetique": True},
                       headers=hdr(csrf)).status_code == 201


def test_collab_lit_offres(client):
    auth(client, "collab")
    assert client.get("/api/offres").status_code == 200


def test_collab_atteint_candidature_puis_400(client):
    # collab est autorisé (rôle) -> passe le guard -> 400 (offre bidon), PAS 403
    csrf = auth(client, "collab")
    r = client.post("/api/candidatures", json={"offre_id": 999999, "profil_id": 999999},
                    headers=hdr(csrf))
    assert r.status_code == 400


# ---- 5. CSRF obligatoire sur les mutations ------------------------------------
def test_csrf_obligatoire(client):
    csrf = auth(client, "rh")
    # authentifié mais SANS en-tête CSRF -> 403
    assert client.post("/api/profils", json={"nom": "NoCSRF"}).status_code == 403
    # avec en-tête -> 201
    assert client.post("/api/profils", json={"nom": "WithCSRF"}, headers=hdr(csrf)).status_code == 201


# ---- 6. Identité côté serveur : decided_by = session --------------------------
def test_decided_by_vient_de_la_session(client):
    csrf_rh = auth(client, "rh")
    off = client.post("/api/offres", json={"titre": "Poste Z", "type": "offre_poste"},
                      headers=hdr(csrf_rh))
    assert off.status_code == 201, off.text
    prof = client.post("/api/profils", json={"nom": "Cand", "synthetique": True},
                       headers=hdr(csrf_rh))
    assert prof.status_code == 201, prof.text
    rh_id = client.get("/api/auth/me").json()["id"]

    # collab dépose la candidature
    csrf_c = auth(client, "collab")
    cand = client.post("/api/candidatures",
                       json={"offre_id": off.json()["id"], "profil_id": prof.json()["id"]},
                       headers=hdr(csrf_c))
    assert cand.status_code == 201, cand.text
    cid = cand.json()["id"]

    # RH décide en tentant d'injecter un decided_by bidon -> ignoré, on prend la session
    csrf_rh = auth(client, "rh")
    dec = client.patch(f"/api/candidatures/{cid}/decision",
                       json={"statut": "retenue", "decided_by": 999999}, headers=hdr(csrf_rh))
    assert dec.status_code == 200, dec.text
    assert dec.json()["statut"] == "retenue"
    assert dec.json()["decided_by"] == rh_id  # session, pas le 999999 du client
