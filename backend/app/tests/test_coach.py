#!/usr/bin/env python3
"""
tests/test_coach.py — Coach Carrière (chat contextualisé). Teste sans Ollama :
`generate` est monkeypatché pour capturer le prompt/system construits.
"""

from app.services import coach_service as cs
from app.schemas.coach import CoachMessage
from app.models.user import User, Role
from app.models.profil import Profil, ProfilCompetence


def _make_collab(db, email: str, **profil_kw) -> User:
    u = User(email=email, name="Coach Test", role=Role.COLLAB)
    db.add(u)
    db.flush()
    p = Profil(user_id=u.id, nom=profil_kw.pop("nom", "Test"), synthetique=True, **profil_kw)
    db.add(p)
    db.flush()
    return u, p


def test_coach_injecte_le_profil_reel(db, monkeypatch):
    u, p = _make_collab(db, "coach1@bmci.local", prenom="Marc",
                        poste_actuel="Conseiller", aspirations="Devenir manager risques")
    db.add(ProfilCompetence(profil_id=p.id, libelle="Analyse crédit", niveau=4))
    db.commit()

    cap = {}

    def fake_generate(task, prompt, system="", is_valid=None):
        cap.update(task=task, prompt=prompt, system=system)
        return "Voici un premier conseil."

    monkeypatch.setattr(cs, "generate", fake_generate)
    out = cs.chat(db, u.id, "Comment évoluer ?", [])

    assert out["reply"] == "Voici un premier conseil."
    assert cap["task"] == "coach"
    # Profil réel injecté ET fencé comme donnée (anti-injection).
    assert "Devenir manager risques" in cap["system"]
    assert "Analyse crédit" in cap["system"]
    assert "<donnee>" in cap["system"]
    assert "Comment évoluer ?" in cap["prompt"]


def test_coach_repli_si_llm_indisponible(db, monkeypatch):
    u, _ = _make_collab(db, "coach2@bmci.local")
    db.commit()
    monkeypatch.setattr(cs, "generate", lambda *a, **k: "")  # LLM muet
    out = cs.chat(db, u.id, "Bonjour", [])
    assert "indisponible" in out["reply"].lower()


def test_coach_historique_dans_le_prompt(db, monkeypatch):
    u, _ = _make_collab(db, "coach3@bmci.local")
    db.commit()
    cap = {}

    def fake_generate(task, prompt, system="", is_valid=None):
        cap["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(cs, "generate", fake_generate)
    history = [CoachMessage(role="user", content="Bonjour"),
               CoachMessage(role="assistant", content="Bonjour, comment puis-je aider ?")]
    cs.chat(db, u.id, "Quelles sont mes forces ?", history)
    assert "Bonjour" in cap["prompt"]
    assert "Quelles sont mes forces ?" in cap["prompt"]
