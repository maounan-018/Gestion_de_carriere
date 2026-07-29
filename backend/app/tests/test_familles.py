#!/usr/bin/env python3
"""
tests/test_familles.py — Cartographie enrichie par FAMILLE de compétences.

Unitaire (logique de tension déterministe sur une base contrôlée) + e2e (RBAC RH,
structure de la réponse).
"""

from app.tests.conftest import auth


def test_familles_tension_deterministe(db):
    from app.services import dashboard_service as ds
    from app.models.profil import Profil, ProfilCompetence
    from app.models.offre import Offre, OffreCompetence, OffreStatut

    p = Profil(nom="X", departement_key="d")
    db.add(p)
    db.flush()
    # Famille "metier" : 1 profil la détient, 3 attendus demandés (offre OUVERTE) -> forte.
    db.add(ProfilCompetence(profil_id=p.id, libelle="c1", categorie="metier", niveau=4))
    o = Offre(titre="O", statut=OffreStatut.OUVERTE)
    db.add(o)
    db.flush()
    for i in range(3):
        db.add(OffreCompetence(offre_id=o.id, libelle=f"a{i}", categorie="metier"))
    # Famille "outil_technologie" : détenue mais non demandée -> faible.
    db.add(ProfilCompetence(profil_id=p.id, libelle="c2", categorie="outil_technologie", niveau=3))
    db.commit()

    res = {f.famille: f for f in ds.familles(db)}
    assert res["metier"].demande == 3
    assert res["metier"].profils_couverts == 1
    assert res["metier"].detenues == 1
    assert res["metier"].tension == "forte"            # 1 profil pour 3 attendus -> ratio < 1
    assert res["outil_technologie"].demande == 0
    assert res["outil_technologie"].tension == "faible"


def test_familles_reservee_rh(client):
    auth(client, "collab")
    assert client.get("/api/dashboards/familles").status_code == 403


def test_familles_structure_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/familles")
    assert r.status_code == 200
    fams = r.json()
    assert isinstance(fams, list) and fams            # le seed a des compétences détenues
    for f in fams:
        assert {"famille", "detenues", "profils_couverts",
                "niveau_moyen", "demande", "tension"} <= set(f)
        assert f["tension"] in ("faible", "moyenne", "forte")
