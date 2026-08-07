#!/usr/bin/env python3
"""
tests/test_succession.py — Plan de succession CALCULÉ (déterministe, sans LLM).
Teste le recouvrement pondéré de compétences : couverture, poste à risque, pôle vide.
"""

import time

from app.services import succession_service as ss
from app.models.profil import Profil, ProfilCompetence
from app.tests.conftest import auth, hdr


def test_succession_calculee_couverture(db):
    """Un poste d'encadrement dont un collaborateur couvre les compétences →
    successeur viable identifié, poste non à risque, écarts calculés."""
    holder = Profil(nom="Alami", prenom="Nadia", poste_actuel="Responsable RH",
                    departement_key="rh", synthetique=True)
    cand = Profil(nom="El Amrani", prenom="Youssef", poste_actuel="Conseiller RH",
                  departement_key="rh", synthetique=True)
    db.add_all([holder, cand])
    db.flush()
    db.add_all([
        ProfilCompetence(profil_id=holder.id, libelle="Gestion des talents", niveau=5),
        ProfilCompetence(profil_id=holder.id, libelle="Recrutement", niveau=4),
        ProfilCompetence(profil_id=cand.id, libelle="Gestion des talents", niveau=4),
        ProfilCompetence(profil_id=cand.id, libelle="Recrutement", niveau=4),
    ])
    db.commit()

    out = ss.plan_succession(db, "rh")

    assert out["effectif"] == 2
    assert out["postes_cles"] == 1          # seul "Responsable RH" est un poste clé
    assert out["couverts"] == 1
    assert out["a_risque"] == 0
    role = out["roles"][0]
    assert role["titulaire"] == "Nadia Alami"
    assert role["risque"] is False
    succ = role["successeurs"][0]
    assert succ["nom"] == "Youssef El Amrani"
    # couvert = min(4,5)+min(4,4)=8 ; total=9 → round(100*8/9)=89 → « Prêt »
    assert succ["score"] == 89
    assert succ["readiness"] == "Prêt"
    assert "Gestion des talents" in succ["ecarts"]   # niveau 4 < 5 du titulaire


def test_succession_poste_a_risque(db):
    """Un poste d'encadrement sans collaborateur au profil compatible → À RISQUE."""
    holder = Profil(nom="Bennis", prenom="Salma", poste_actuel="Directrice Financière",
                    departement_key="fin", synthetique=True)
    cand = Profil(nom="Ouzzine", prenom="Karim", poste_actuel="Agent d'accueil",
                  departement_key="fin", synthetique=True)
    db.add_all([holder, cand])
    db.flush()
    db.add_all([
        ProfilCompetence(profil_id=holder.id, libelle="Trésorerie", niveau=5),
        ProfilCompetence(profil_id=cand.id, libelle="Accueil", niveau=2),
    ])
    db.commit()

    out = ss.plan_succession(db, "fin")

    assert out["postes_cles"] == 1
    assert out["a_risque"] == 1
    assert out["couverts"] == 0
    role = out["roles"][0]
    assert role["risque"] is True
    assert role["successeurs"] == []


def test_pole_vide(db):
    out = ss.plan_succession(db, "pole_inconnu")
    assert out["effectif"] == 0
    assert out["roles"] == []
    assert out["postes_cles"] == 0
    assert "Aucun poste d'encadrement" in out["synthese"]


# ---------------------------------------------------------- Version ASYNCHRONE

def test_succession_async_flux(client, monkeypatch):
    """POST /succession/async → job_id, puis GET /jobs/{id} → done + résultat.
    `plan_succession` mocké (rapide) : on teste le flux/RBAC, pas Ollama."""
    from app.services import succession_service
    monkeypatch.setattr(succession_service, "plan_succession",
                        lambda db, dk: {"departement_key": dk, "effectif": 3,
                                        "plan": "Plan mocké.", "model": "test"})
    csrf = auth(client, "rh")
    r = client.post("/api/rh/succession/async",
                    json={"departement_key": "retail_banking"}, headers=hdr(csrf))
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]

    body = None
    for _ in range(60):
        s = client.get(f"/api/rh/succession/jobs/{job_id}")
        assert s.status_code == 200
        body = s.json()
        if body["status"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert body is not None and body["status"] == "done", body
    assert body["result"]["plan"] == "Plan mocké."
    assert body["result"]["effectif"] == 3


def test_succession_async_reserve_aux_rh(client):
    """Un collaborateur ne peut pas lancer un plan de succession (RBAC RH/ADMIN)."""
    csrf = auth(client, "collab")
    r = client.post("/api/rh/succession/async",
                    json={"departement_key": "retail_banking"}, headers=hdr(csrf))
    assert r.status_code == 403


def test_succession_job_inconnu_404(client):
    auth(client, "rh")
    r = client.get("/api/rh/succession/jobs/inexistant")
    assert r.status_code == 404
