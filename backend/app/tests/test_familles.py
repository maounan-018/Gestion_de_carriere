#!/usr/bin/env python3
"""
tests/test_familles.py — Cartographie enrichie par FAMILLE de compétences.

Unitaire (logique de tension déterministe sur une base contrôlée) + e2e (RBAC RH,
structure de la réponse).
"""

from app.tests.conftest import auth


def test_familles_tension_deterministe(db):
    """Tension par famille = écart entre l'ATTENDU (= effectif : chaque collaborateur
    est censé maîtriser un socle) et la COUVERTURE (profils compétents, niveau ≥ 4).
    Indépendant des offres ouvertes (cf. refonte cartographie)."""
    from app.models.profil import Profil, ProfilCompetence
    from app.services import dashboard_service as ds

    profils = [Profil(nom=f"P{i}", departement_key="d") for i in range(4)]
    db.add_all(profils)
    db.flush()
    # Famille "metier" : 1 seul profil compétent sur 4 -> ratio 0.25 -> forte.
    db.add(ProfilCompetence(profil_id=profils[0].id, libelle="c1", categorie="metier", niveau=5))
    # Famille "comportementale" : les 4 profils compétents -> ratio 1.0 -> faible.
    for p in profils:
        db.add(
            ProfilCompetence(profil_id=p.id, libelle="soft", categorie="comportementale", niveau=4)
        )
    db.commit()

    res = {f.famille: f for f in ds.familles(db)}
    assert res["metier"].demande == 4  # ATTENDU = effectif
    assert res["metier"].detenues == 1
    assert res["metier"].profils_couverts == 1
    assert res["metier"].tension == "forte"  # 1/4 couverts
    assert res["comportementale"].demande == 4
    assert res["comportementale"].profils_couverts == 4
    assert res["comportementale"].tension == "faible"  # 4/4 couverts


def test_familles_reservee_rh(client):
    auth(client, "collab")
    assert client.get("/api/dashboards/familles").status_code == 403


def test_familles_structure_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/familles")
    assert r.status_code == 200
    fams = r.json()
    assert isinstance(fams, list) and fams  # le seed a des compétences détenues
    for f in fams:
        assert {
            "famille",
            "detenues",
            "profils_couverts",
            "niveau_moyen",
            "demande",
            "tension",
        } <= set(f)
        assert f["tension"] in ("faible", "moyenne", "forte")
