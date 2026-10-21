#!/usr/bin/env python3
"""
tests/test_normalisation.py — Normalisation de libellés de compétences (tâche IA).
Teste sans Ollama : `generate` monkeypatché. Vérifie le post-traitement défensif.
"""

from app.services import normalisation_service as ns


def test_regroupe_et_canonicalise(monkeypatch):
    monkeypatch.setattr(
        ns,
        "generate",
        lambda *a, **k: {
            "groupes": [
                {
                    "canonique": "Gestion de projet",
                    "variantes": ["gestion projet", "Project Management"],
                },
            ]
        },
    )
    out = ns.normaliser(["gestion projet", "Project Management", "Python"])
    canon = {g["canonique"] for g in out["groupes"]}
    assert "Gestion de projet" in canon
    assert "Python" in canon  # non couvert par le LLM -> groupe identité
    # Couverture exhaustive, chaque libellé une seule fois.
    plat = sorted(v for g in out["groupes"] for v in g["variantes"])
    assert plat == sorted(["gestion projet", "Project Management", "Python"])


def test_ignore_les_variantes_hallucinees(monkeypatch):
    monkeypatch.setattr(
        ns,
        "generate",
        lambda *a, **k: {
            "groupes": [
                {"canonique": "X", "variantes": ["a", "INVENTÉ PAR LE MODÈLE"]},
            ]
        },
    )
    out = ns.normaliser(["a"])
    plat = [v for g in out["groupes"] for v in g["variantes"]]
    assert plat == ["a"]  # la variante absente de l'entrée est rejetée


def test_repli_identite_si_llm_indisponible(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(ns, "generate", boom)
    out = ns.normaliser(["Analyse crédit", "Leadership"])
    assert len(out["groupes"]) == 2
    assert {g["canonique"] for g in out["groupes"]} == {"Analyse crédit", "Leadership"}


def test_liste_vide():
    out = ns.normaliser(["  ", ""])
    assert out["groupes"] == []
