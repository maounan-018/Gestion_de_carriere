#!/usr/bin/env python3
"""tests/test_recommandation_persistence.py — Persistance de la reco (Lot B7).

Vérifie que la reco est ÉCRITE en base (source durable) et relue, et qu'un
recalcul du MÊME état (même signature) met à jour la ligne au lieu d'en créer
une nouvelle (« recalcul = mise à jour, jamais une perte »)."""

from sqlalchemy import select

from app.services import recommendation_service as rs
from app.models.recommandation import Recommandation

_RES = {
    "poste_vise": "Manager d'équipe Risques", "score_actuel": 40,
    "competences_a_developper": [{"competence": "Leadership"}],
    "passerelles_metiers": [], "plan_developpement": "Plan de dev.", "confiance": "clair",
}


def test_persistance_reco_roundtrip_et_upsert(db):
    sig = "signature-test-b7"
    rs._persister_reco(db, 1, sig, "Manager d'équipe Risques", _RES)

    loaded = rs._charger_reco_persistee(db, sig)
    assert loaded is not None
    assert loaded["score_actuel"] == 40
    assert loaded["poste_vise"] == "Manager d'équipe Risques"

    # Recalcul du même état (même signature) → MISE À JOUR, pas de doublon.
    rs._persister_reco(db, 1, sig, "Manager d'équipe Risques", {**_RES, "score_actuel": 60})
    rows = db.scalars(select(Recommandation).where(Recommandation.signature == sig)).all()
    assert len(rows) == 1
    assert rows[0].score == 60


def test_charger_reco_absente_renvoie_none(db):
    assert rs._charger_reco_persistee(db, "signature-inexistante") is None
