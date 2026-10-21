#!/usr/bin/env python3
"""
tests/test_synthese_rh.py — Synthèse RH consolidée (GET /api/dashboards/synthese).

Unitaire (agrégations déterministes) + e2e (RBAC RH, structure).
"""

from app.tests.conftest import auth


def test_synthese_agrege_effectifs_et_pipeline(db):
    from app.models.candidature import Candidature, CandidatureStatut
    from app.models.offre import Offre
    from app.models.profil import Profil
    from app.services import dashboard_service as ds

    db.add_all(
        [
            Profil(nom="A", departement_key="risques"),
            Profil(nom="B", departement_key="risques"),
            Profil(nom="C", departement_key="retail_banking"),
        ]
    )
    o = Offre(titre="O")
    p = Profil(nom="X", departement_key="risques")
    db.add_all([o, p])
    db.flush()
    db.add(Candidature(offre_id=o.id, profil_id=p.id, statut=CandidatureStatut.RETENUE))
    db.commit()

    s = ds.synthese(db)
    assert s["effectif"] == 4
    poles = {x["pole"]: x["effectif"] for x in s["par_pole"]}
    assert poles.get("Risques") == 3  # 3 profils dans « risques » (humanisé)
    statuts = {x["statut"]: x["nombre"] for x in s["candidatures_par_statut"]}
    assert statuts.get("retenue") == 1
    assert isinstance(s["familles_en_tension"], int)


def test_synthese_reservee_rh(client):
    auth(client, "collab")
    assert client.get("/api/dashboards/synthese").status_code == 403


def test_synthese_structure_rh(client):
    auth(client, "rh")
    r = client.get("/api/dashboards/synthese")
    assert r.status_code == 200
    b = r.json()
    assert {"effectif", "par_pole", "candidatures_par_statut", "familles_en_tension"} <= set(b)
    assert isinstance(b["par_pole"], list)
