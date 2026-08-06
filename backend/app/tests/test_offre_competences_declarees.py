"""Vérifie que les compétences DÉCLARÉES par le manager à la publication sont
stockées telles quelles (mission sans fiche) — Workstream B."""

from app.tests.conftest import auth, hdr


def test_mission_stocke_les_competences_declarees(client):
    csrf = auth(client, "manager")
    body = {
        "titre": "[T] Mission risques", "type": "mission", "statut": "brouillon",
        "fiche_id": None, "heriter_competences": False,
        "competences": [
            {"libelle": "gestion des risques", "skill_id": None, "importance": "essentielle"},
            {"libelle": "communication", "skill_id": None, "importance": "souhaitee"},
        ],
        "synthetique": True,
    }
    r = client.post("/api/offres", json=body, headers=hdr(csrf))
    assert r.status_code == 201, r.text
    oid = r.json()["id"]
    detail = client.get(f"/api/offres/{oid}").json()
    libelles = sorted(c["libelle"] for c in detail["competences"])
    assert libelles == ["communication", "gestion des risques"], libelles
