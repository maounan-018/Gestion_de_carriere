#!/usr/bin/env python3
"""
tests/test_reco_robustesse.py — Robustesse de la reco aux entrées bruitées :
normalisation d'entrée + gate d'ancrage + dégradation gracieuse. Sans Ollama
(LLM monkeypatché).
"""

from app.models.profil import Profil
from app.models.user import Role, User
from app.services import input_normalization_service as ins
from app.services import recommendation_service as rs
from app.services import skill_matching_service as sms
from app.tests.conftest import anon, auth, hdr

# ------------------------------------------------------- Normalisation d'entrée


def test_norm_trop_court_ambigu():
    assert ins.normaliser_cible("ab")["confiance"] == "ambigu"
    assert ins.normaliser_cible("")["confiance"] == "ambigu"


def test_norm_clair(monkeypatch):
    monkeypatch.setattr(
        ins,
        "generate",
        lambda *a, **k: {"intitule": "Chargé d'affaires professionnels", "confiance": "clair"},
    )
    r = ins.normaliser_cible("chargé daffaire pro (edit rh test)")
    assert r["confiance"] == "clair"
    assert r["intitule"] == "Chargé d'affaires professionnels"  # pollution retirée


def test_norm_ambigu_du_llm(monkeypatch):
    monkeypatch.setattr(ins, "generate", lambda *a, **k: {"intitule": "zzz", "confiance": "ambigu"})
    assert ins.normaliser_cible("asdkjh qwe zzz")["confiance"] == "ambigu"


def test_norm_indisponible_ne_bloque_pas(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(ins, "generate", boom)
    r = ins.normaliser_cible("un objectif de carrière suffisamment long")
    assert r["confiance"] == "indisponible"  # panne signalée
    assert r["intitule"] == "un objectif de carrière suffisamment long"  # brut conservé


# ------------------------------------------------------------ Gate d'ancrage


def _extraction(matches0):
    return {
        "skills": [
            {"raw": "Analyse situation", "importance": "essentielle", "matches": [matches0]},
            {
                "raw": "Négociation",
                "importance": "essentielle",
                "matches": [
                    {
                        "label_fr": "Négociation commerciale",
                        "skill_id": 7,
                        "skill_type": "t",
                        "rerank_score": 0.82,
                    }
                ],
            },
        ]
    }


def test_gate_rejette_ancrage_faible():
    ex = sms.build_exigences(
        _extraction(
            {
                "label_fr": "évaluer l'état de navires",
                "skill_id": 99,
                "skill_type": "t",
                "rerank_score": 0.04,
            }
        ),
        min_ancrage=0.35,
    )
    # ancrage faible rejeté -> libellé BRUT conservé (fidèle), non ancré
    assert ex[0]["competence"] == "Analyse situation" and ex[0]["skill_id"] is None
    # ancrage fort conservé -> libellé canonique
    assert ex[1]["competence"] == "Négociation commerciale" and ex[1]["skill_id"] == 7


def test_gate_off_par_defaut():
    ex = sms.build_exigences(
        _extraction(
            {
                "label_fr": "évaluer l'état de navires",
                "skill_id": 99,
                "skill_type": "t",
                "rerank_score": 0.04,
            }
        )
    )
    assert ex[0]["competence"] == "évaluer l'état de navires"  # min_ancrage=0.0 -> pas de gate


# ------------------------------------------------------ Dégradation gracieuse


def test_reco_ambigu_demande_de_preciser(db, monkeypatch):
    u = User(email="amb@bmci.local", name="Ambigu", role=Role.COLLAB)
    db.add(u)
    db.flush()
    db.add(Profil(user_id=u.id, nom="X", aspirations="???", synthetique=True))
    db.commit()

    monkeypatch.setattr(
        rs, "normaliser_cible", lambda t: {"intitule": t, "confiance": "ambigu", "model": "test"}
    )
    called = {"n": 0}
    monkeypatch.setattr(rs, "recommander", lambda *a, **k: called.__setitem__("n", called["n"] + 1))

    out = rs.recommander_pour_user(db, u.id)
    assert called["n"] == 0  # ni extraction ni conseil
    assert out["competences_a_developper"] == []
    assert out["confiance"] == "ambigu"  # signalé pour le bandeau UI
    assert "précis" in out["plan_developpement"].lower()  # message de clarification


# -------------------------------------------------- Endpoint outil réutilisable


def test_normalisation_cible_endpoint(client, monkeypatch):
    from app.services import input_normalization_service

    monkeypatch.setattr(
        input_normalization_service,
        "normaliser_cible",
        lambda t: {
            "intitule": "Chargé d'affaires professionnels",
            "confiance": "clair",
            "model": "test",
        },
    )
    csrf = auth(client, "collab")
    r = client.post(
        "/api/normalisation/cible",
        json={"texte": "chargé daffaire (edit rh test)"},
        headers=hdr(csrf),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["intitule"] == "Chargé d'affaires professionnels"
    assert body["confiance"] == "clair"


def test_normalisation_cible_exige_auth(client):
    anon(client)
    r = client.post("/api/normalisation/cible", json={"texte": "x"})
    assert r.status_code in (401, 403)
