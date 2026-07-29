#!/usr/bin/env python3
"""
tests/test_succession.py — Plan de succession (tâche IA `raisonnement_batch`).
Teste sans Ollama (`generate` monkeypatché) : contexte réel + repli + pôle vide.
"""

from app.services import succession_service as ss
from app.models.profil import Profil, ProfilCompetence


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
