#!/usr/bin/env python3
"""
tests/test_ownership.py — Ownership ligne-à-ligne (B2), de bout en bout.

Prouve le cloisonnement par PÉRIMÈTRE (au-delà du RBAC) sur profils & candidatures :
  - COLLAB  : SON profil / SES candidatures uniquement ;
  - MANAGER : lui + SON ÉQUIPE (le collab El Amrani est managé par le manager) ;
  - RH/ADMIN : global.
Les ids « hors périmètre » sont des personas synthétiques (user_id NULL), invisibles
aux managers. Découverte des ids faite en tant que RH (périmètre global).
"""

from app.tests.conftest import auth, hdr


# ------------------------------------------------------------------ Profils

def test_collab_lit_son_profil_pas_celui_dautrui(client):
    auth(client, "rh")
    profils = client.get("/api/profils").json()
    autre = next(p["id"] for p in profils if p["nom"] != "El Amrani")  # pas le profil du collab

    auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    assert client.get(f"/api/profils/{mon}").status_code == 200            # son profil
    assert client.get(f"/api/profils/{autre}/carriere").status_code == 403  # profil d'autrui


def test_manager_lit_equipe_pas_hors_equipe(client):
    csrf = auth(client, "rh")
    profils = client.get("/api/profils").json()
    bennani = next(p["id"] for p in profils if p["nom"] == "El Amrani")       # équipe du manager
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
    assert any(p["nom"] == "El Amrani" for p in profils)


def test_manager_voit_candidat_de_son_offre_hors_equipe(client, monkeypatch):
    """Périmètre par OFFRE : le manager consulte la fiche/CV d'un candidat à une
    offre QU'IL A PUBLIÉE, même si ce candidat n'est pas dans son équipe."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "MANAGER_PEUT_PUBLIER", True)  # le manager publie ici
    # Le manager publie une offre (created_by = lui, côté serveur).
    csrf_mgr = auth(client, "manager")
    off = client.post("/api/offres", json={"titre": "Mission Revue", "type": "mission"},
                      headers=hdr(csrf_mgr)).json()["id"]
    # RH (global) crée un candidat synthétique hors équipe + sa candidature à l'offre.
    csrf_rh = auth(client, "rh")
    synth = client.post("/api/profils", json={"nom": "CandidatRevue", "synthetique": True},
                        headers=hdr(csrf_rh)).json()["id"]
    client.post("/api/candidatures", json={"offre_id": off, "profil_id": synth},
                headers=hdr(csrf_rh))

    # Le manager : hors offre le profil reste invisible, mais candidat à SON offre → 200.
    auth(client, "manager")
    assert client.get(f"/api/profils/{synth}/carriere").status_code == 200
    # La liste des candidats de l'offre expose le champ cv_filename (aperçu CV).
    cands = client.get(f"/api/offres/{off}/candidats")
    assert cands.status_code == 200, cands.text
    assert any(c["profil_id"] == synth and "cv_filename" in c for c in cands.json())


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


# --------------------------------------------------------- Retrait candidature

def test_collab_retire_sa_candidature(client):
    # RH publie une offre ; le collab candidate pour SON profil puis la retire.
    csrf_rh = auth(client, "rh")
    off = client.post("/api/offres", json={"titre": "Poste Retrait", "type": "offre_poste"},
                      headers=hdr(csrf_rh)).json()["id"]
    csrf = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    cand = client.post("/api/candidatures", json={"offre_id": off, "profil_id": mon},
                       headers=hdr(csrf)).json()["id"]
    r = client.patch(f"/api/candidatures/{cand}/retrait", headers=hdr(csrf))
    assert r.status_code == 200, r.text
    assert r.json()["statut"] == "retiree"


def test_collab_ne_retire_pas_candidature_dautrui(client):
    # RH crée une candidature pour un profil synthétique ; le collab ne peut pas la retirer.
    csrf_rh = auth(client, "rh")
    off = client.post("/api/offres", json={"titre": "Poste RetraitX", "type": "offre_poste"},
                      headers=hdr(csrf_rh)).json()["id"]
    synth = client.post("/api/profils", json={"nom": "CandRetrait", "synthetique": True},
                        headers=hdr(csrf_rh)).json()["id"]
    cand = client.post("/api/candidatures", json={"offre_id": off, "profil_id": synth},
                       headers=hdr(csrf_rh)).json()["id"]
    csrf = auth(client, "collab")
    r = client.patch(f"/api/candidatures/{cand}/retrait", headers=hdr(csrf))
    assert r.status_code == 403, r.text


# --------------------------------------------------- Notification ciblée (RH → collab)

def test_rh_notifie_un_collaborateur(client):
    # RH envoie une notification ciblée au collab (Youssef a un compte → délivrée).
    auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    csrf = auth(client, "rh")
    r = client.post("/api/notifications/message-profil", headers=hdr(csrf),
                    json={"profil_id": mon, "sujet": "Créneau",
                          "message": "Un créneau d'entretien vous est proposé."})
    assert r.status_code == 200, r.text
    assert r.json()["delivered"] is True


def test_message_profil_synthetique_non_delivre(client):
    # Profil synthétique sans compte → delivered=False (pas d'erreur).
    csrf = auth(client, "rh")
    synth = client.post("/api/profils", json={"nom": "SynthNotif", "synthetique": True},
                        headers=hdr(csrf)).json()["id"]
    r = client.post("/api/notifications/message-profil", headers=hdr(csrf),
                    json={"profil_id": synth, "message": "test"})
    assert r.status_code == 200, r.text
    assert r.json()["delivered"] is False


def test_message_profil_interdit_au_collab(client):
    # Un COLLAB ne peut pas notifier un autre collaborateur (RBAC → 403).
    csrf = auth(client, "collab")
    mon = client.get("/api/profils/me/carriere").json()["profil_id"]
    r = client.post("/api/notifications/message-profil", headers=hdr(csrf),
                    json={"profil_id": mon, "message": "test"})
    assert r.status_code == 403
