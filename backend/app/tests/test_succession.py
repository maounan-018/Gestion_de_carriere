#!/usr/bin/env python3
"""
tests/test_succession.py — Plan de succession (tâche IA `raisonnement_batch`).
Teste sans Ollama (`generate` monkeypatché) : contexte réel + repli + pôle vide.
"""

import time

from app.services import succession_service as ss
from app.models.profil import Profil, ProfilCompetence
from app.tests.conftest import auth, hdr


def test_contexte_reel_du_pole(db, monkeypatch):
    p1 = Profil(nom="Alami", prenom="Nadia", poste_actuel="Responsable RH",
                departement_key="rh", aspirations="Directrice des Talents", synthetique=True)
    p2 = Profil(nom="Bennani", prenom="Marc", poste_actuel="Conseiller",
                departement_key="rh", synthetique=True)
    db.add_all([p1, p2])
    db.flush()
    db.add(ProfilCompetence(profil_id=p1.id, libelle="Gestion des talents", niveau=5))
    db.commit()

    cap = {}

    def fake_generate(task, prompt, system="", is_valid=None):
        cap.update(task=task, prompt=prompt, system=system)
        return "Plan de succession détaillé."

    monkeypatch.setattr(ss, "generate", fake_generate)
    out = ss.plan_succession(db, "rh")

    assert out["effectif"] == 2
    assert out["plan"] == "Plan de succession détaillé."
    assert cap["task"] == "raisonnement_batch"
    # Données réelles du pôle injectées ET fencées.
    assert "Nadia Alami" in cap["prompt"]
    assert "Gestion des talents" in cap["prompt"]
    assert "<donnee>" in cap["prompt"]


def test_repli_si_indisponible(db, monkeypatch):
    db.add(Profil(nom="X", departement_key="rh", synthetique=True))
    db.commit()

    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(ss, "generate", boom)
    out = ss.plan_succession(db, "rh")
    assert "indisponible" in out["plan"].lower()


def test_pole_vide(db, monkeypatch):
    monkeypatch.setattr(ss, "generate", lambda task, prompt, system="", is_valid=None: prompt)
    out = ss.plan_succession(db, "pole_inconnu")
    assert out["effectif"] == 0
    assert "Aucun collaborateur" in out["plan"]  # le prompt (échoé) contient le contexte vide


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
