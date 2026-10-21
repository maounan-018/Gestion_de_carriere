"""Workflow besoin de recrutement : manager exprime → HRBP publie en continuité
→ visibilité partagée (le manager voit l'offre née de son besoin)."""

from app.tests.conftest import auth, hdr


def test_manager_publie_directement_interdit(client):
    # Flag off (défaut) : le manager ne publie pas directement.
    csrf = auth(client, "manager")
    r = client.post("/api/offres", json={"titre": "X", "type": "mission"}, headers=hdr(csrf))
    assert r.status_code == 403


def test_besoin_workflow_visibilite_partagee(client):
    # 1) Manager exprime un besoin
    csrf_m = auth(client, "manager")
    b = client.post(
        "/api/besoins",
        json={"poste": "Analyste crédit", "description": "Renfort équipe risques"},
        headers=hdr(csrf_m),
    )
    assert b.status_code == 201, b.text
    bid = b.json()["id"]
    assert b.json()["statut"] == "transmis"
    assert any(x["id"] == bid for x in client.get("/api/besoins/mes").json())

    # 2) HRBP le voit et publie l'offre en continuité
    csrf_rh = auth(client, "rh")
    assert any(x["id"] == bid for x in client.get("/api/besoins").json())
    pub = client.post(f"/api/besoins/{bid}/publier", json={}, headers=hdr(csrf_rh))
    assert pub.status_code == 200, pub.text
    offre_id = pub.json()["id"]

    # 3) Le besoin est relié à l'offre et marqué publié
    auth(client, "manager")
    mine = {x["id"]: x for x in client.get("/api/besoins/mes").json()}
    assert mine[bid]["statut"] == "publie"
    assert mine[bid]["offre_id"] == offre_id

    # 4) Visibilité PARTAGÉE : le manager d'origine voit l'offre publiée par la HRBP
    mo = client.get("/api/offres/mes-offres").json()
    assert any(o["id"] == offre_id for o in mo)
