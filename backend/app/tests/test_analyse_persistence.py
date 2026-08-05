#!/usr/bin/env python3
"""tests/test_analyse_persistence.py — Persistance de l'analyse stratégique HRBP (Lot 7).

Vérifie que la synthèse IA est ÉCRITE en base (source durable) et relue, et
qu'un recalcul met à jour la MÊME ligne (une seule ligne « courante » par
périmètre) — le tableau de bord HRBP présente ainsi l'analyse courante sans
relancer le LLM."""

from sqlalchemy import select

from app.services import analyse_service as asv
from app.models.analyse_rh import AnalyseRh


def test_persistance_analyse_roundtrip_et_upsert(db):
    asv._persister(db, "Synthèse v1.", "mistral-nemo")

    loaded = asv.charger_derniere(db)
    assert loaded is not None
    assert loaded["synthese"] == "Synthèse v1."
    assert loaded["model"] == "mistral-nemo"
    assert loaded["genere_le"]  # horodatage présent

    # Recalcul → MISE À JOUR de la ligne courante, pas de doublon.
    asv._persister(db, "Synthèse v2.", "mistral-nemo")
    rows = db.scalars(select(AnalyseRh).where(AnalyseRh.scope == "global")).all()
    assert len(rows) == 1
    assert rows[0].synthese == "Synthèse v2."


def test_charger_analyse_absente_renvoie_none(db):
    assert asv.charger_derniere(db) is None
