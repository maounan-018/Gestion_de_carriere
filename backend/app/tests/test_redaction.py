#!/usr/bin/env python3
"""
tests/test_redaction.py — Aide à la rédaction (tâche IA `redaction`).
Teste sans Ollama : `generate` monkeypatché.
"""

from app.services import redaction_service as rs


def test_resume(monkeypatch):
    cap = {}

    def fake_generate(task, prompt, system="", is_valid=None):
        cap.update(task=task, system=system, prompt=prompt)
        return "  Synthèse concise.  "

    monkeypatch.setattr(rs, "generate", fake_generate)
    out = rs.rediger("Un long texte de bilan…", mode="resume")
    assert out["texte"] == "Synthèse concise."  # trim appliqué
    assert out["mode"] == "resume"
    assert cap["task"] == "redaction"
    assert "RÉSUME" in cap["system"]
    assert "<donnee>" in cap["prompt"]  # source fencée


def test_reformulation(monkeypatch):
    cap = {}
    monkeypatch.setattr(rs, "generate",
                        lambda t, p, system="", is_valid=None: cap.update(system=system) or "Version reformulée.")
    out = rs.rediger("txt", mode="reformulation", consignes="ton formel")
    assert out["texte"] == "Version reformulée."
    assert out["mode"] == "reformulation"
    assert "REFORMULE" in cap["system"]


def test_mode_invalide_retombe_sur_resume(monkeypatch):
    monkeypatch.setattr(rs, "generate", lambda *a, **k: "ok")
    assert rs.rediger("txt", mode="n_importe_quoi")["mode"] == "resume"


def test_repli_texte_source_si_indisponible(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("ollama down")
    monkeypatch.setattr(rs, "generate", boom)
    out = rs.rediger("Texte original à préserver.")
    assert out["texte"] == "Texte original à préserver."  # repli : source inchangée


def test_retire_balises_donnee_reemises(monkeypatch):
    # mistral-nemo ré-émet parfois les balises de fencing du prompt : on les nettoie.
    monkeypatch.setattr(rs, "generate", lambda *a, **k: "<donnee> Texte reformulé. </donnee>")
    assert rs.rediger("txt", mode="reformulation")["texte"] == "Texte reformulé."


def test_texte_vide():
    assert rs.rediger("   ")["texte"] == ""
