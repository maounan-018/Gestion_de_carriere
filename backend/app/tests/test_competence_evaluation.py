#!/usr/bin/env python3
"""
tests/test_competence_evaluation.py — Moteur d'évaluation des compétences (Lot 8).

Le manager/RH évalue une compétence 1-10 → score PERSISTÉ (source manager) → il
DOMINE le % d'acquisition (poids prépondérant). Sans évaluation, repli sur le
niveau déclaratif (×20). Ownership : manager du profil ou RH/ADMIN.
"""

from app.tests.conftest import anon, auth, hdr


def _profil_avec_competences(client):
    """(profil_id, compétences) d'un profil ayant des compétences (vue RH globale)."""
    auth(client, "rh")
    for p in client.get("/api/profils?limit=60").json():
        comps = client.get(f"/api/profils/{p['id']}").json()["competences"]
        if comps:
            return p["id"], comps
    raise AssertionError("aucun profil avec compétences dans le seed de test")


def test_acquisition_par_defaut_repli_niveau(client):
    _pid, comps = _profil_avec_competences(client)
    scored = [c for c in comps if c["niveau"] is not None]
    assert scored, "attendu des compétences avec niveau"
    c = scored[0]
    assert c["acquisition_pct"] == c["niveau"] * 20  # repli niveau ×20
    assert c["evaluee"] is True


def test_manager_ou_rh_evalue_domine_le_score(client):
    pid, comps = _profil_avec_competences(client)
    cid = comps[0]["id"]
    csrf = auth(client, "rh")  # RH/ADMIN peut évaluer tout profil
    r = client.post(
        f"/api/profils/{pid}/competences/{cid}/evaluation", headers=hdr(csrf), json={"score": 9}
    )
    assert r.status_code == 200, r.text
    comp = next(c for c in r.json()["competences"] if c["id"] == cid)
    assert comp["acquisition_pct"] == 90  # 9 × 10, l'évaluation domine le niveau
    assert comp["evaluee"] is True
    # Persisté : relecture conserve le score.
    again = next(
        c for c in client.get(f"/api/profils/{pid}").json()["competences"] if c["id"] == cid
    )
    assert again["acquisition_pct"] == 90
    # Upsert : ré-évaluer remplace (5/10 → 50 %).
    client.post(
        f"/api/profils/{pid}/competences/{cid}/evaluation", headers=hdr(csrf), json={"score": 5}
    )
    upd = next(c for c in client.get(f"/api/profils/{pid}").json()["competences"] if c["id"] == cid)
    assert upd["acquisition_pct"] == 50


def test_score_hors_bornes_rejete(client):
    pid, comps = _profil_avec_competences(client)
    cid = comps[0]["id"]
    csrf = auth(client, "rh")
    assert (
        client.post(
            f"/api/profils/{pid}/competences/{cid}/evaluation", headers=hdr(csrf), json={"score": 0}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/profils/{pid}/competences/{cid}/evaluation",
            headers=hdr(csrf),
            json={"score": 11},
        ).status_code
        == 422
    )


def test_evaluation_exige_role_hierarchique(client):
    pid, comps = _profil_avec_competences(client)
    cid = comps[0]["id"]
    # Un collaborateur ne peut pas évaluer les compétences d'autrui.
    csrf = auth(client, "collab")
    r = client.post(
        f"/api/profils/{pid}/competences/{cid}/evaluation", headers=hdr(csrf), json={"score": 8}
    )
    assert r.status_code in (403, 404)
    anon(client)
    assert client.post(
        f"/api/profils/{pid}/competences/{cid}/evaluation", json={"score": 8}
    ).status_code in (401, 403)
