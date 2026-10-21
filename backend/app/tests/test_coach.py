#!/usr/bin/env python3
"""
tests/test_coach.py — Coach Carrière (chat contextualisé). Teste sans Ollama :
`generate` est monkeypatché pour capturer le prompt/system construits.
"""

from app.models.profil import Profil, ProfilCompetence
from app.models.user import Role, User
from app.schemas.coach import CoachMessage
from app.services import coach_service as cs


def _make_collab(db, email: str, **profil_kw) -> User:
    u = User(email=email, name="Coach Test", role=Role.COLLAB)
    db.add(u)
    db.flush()
    p = Profil(user_id=u.id, nom=profil_kw.pop("nom", "Test"), synthetique=True, **profil_kw)
    db.add(p)
    db.flush()
    return u, p


def test_coach_injecte_le_profil_reel(db, monkeypatch):
    u, p = _make_collab(
        db,
        "coach1@bmci.local",
        prenom="Youssef",
        poste_actuel="Conseiller",
        aspirations="Devenir manager risques",
    )
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
    history = [
        CoachMessage(role="user", content="Bonjour"),
        CoachMessage(role="assistant", content="Bonjour, comment puis-je aider ?"),
    ]
    cs.chat(db, u.id, "Quelles sont mes forces ?", history)
    assert "Bonjour" in cap["prompt"]
    assert "Quelles sont mes forces ?" in cap["prompt"]


# ---------------------------------------------------------------- Agentique


def test_coach_agentique_appelle_un_outil(db, monkeypatch):
    """Le coach agentique exécute un outil (données réelles) puis répond."""
    u, _ = _make_collab(db, "coach4@bmci.local", aspirations="Manager")
    db.commit()

    calls: list[int] = []
    responses = [
        # Tour 1 : le modèle demande un outil.
        {"tool_calls": [{"function": {"name": "chercher_offres_compatibles", "arguments": {}}}]},
        # Tour 2 : après l'observation, il répond.
        {"content": "D'après les offres internes, voici mon conseil."},
    ]

    def fake_chat_call(model, messages, tools=None, num_ctx=8192, temperature=0):
        calls.append(len(messages))
        return responses[len(calls) - 1]

    monkeypatch.setattr(cs, "chat_call", fake_chat_call)
    out = cs.chat_agent(db, u.id, "Quelles offres pour moi ?", [])

    assert out["reply"] == "D'après les offres internes, voici mon conseil."
    assert "chercher_offres_compatibles" in out["outils"]
    assert len(calls) == 2  # appel outil, puis réponse
    assert calls[1] > calls[0]  # l'observation (role tool) a été ajoutée aux messages


def test_coach_agentique_repli_mono_coup(db, monkeypatch):
    """Si le tool-calling échoue (Ollama down), on retombe sur le mono-coup."""
    u, _ = _make_collab(db, "coach5@bmci.local")
    db.commit()

    def boom(*a, **k):
        raise RuntimeError("ollama indisponible")

    monkeypatch.setattr(cs, "chat_call", boom)
    monkeypatch.setattr(cs, "generate", lambda *a, **k: "Conseil de repli mono-coup.")
    out = cs.chat_agent(db, u.id, "Bonjour", [])
    assert out["reply"] == "Conseil de repli mono-coup."


# ---------------------------------------------------------- Agentique STREAMING


def test_coach_agentique_stream(db, monkeypatch):
    """Le stream émet un événement outil puis les tokens de la réponse, puis 'done'."""
    u, _ = _make_collab(db, "coach6@bmci.local", aspirations="Manager")
    db.commit()

    turns = [
        # Tour 1 : le modèle demande un outil (aucun texte).
        [
            {
                "tool_calls": [
                    {"function": {"name": "chercher_offres_compatibles", "arguments": {}}}
                ],
                "done": True,
            }
        ],
        # Tour 2 : réponse streamée en deux fragments, sans nouvel outil.
        [{"delta": "Voici "}, {"delta": "mon conseil."}, {"tool_calls": [], "done": True}],
    ]
    idx = {"i": 0}

    def fake_chat_stream(model, messages, tools=None, num_ctx=8192, temperature=0):
        chunks = turns[idx["i"]]
        idx["i"] += 1
        yield from chunks

    monkeypatch.setattr(cs, "chat_stream", fake_chat_stream)
    events = list(cs.chat_agent_stream(db, u.id, "Quelles offres pour moi ?", []))

    assert any(e["type"] == "tool" and e["name"] == "chercher_offres_compatibles" for e in events)
    text = "".join(e["text"] for e in events if e["type"] == "token")
    assert text == "Voici mon conseil."
    done = [e for e in events if e["type"] == "done"]
    assert done and "chercher_offres_compatibles" in done[-1]["outils"]


def test_coach_agentique_stream_repli(db, monkeypatch):
    """Si le stream échoue (Ollama down), repli mono-coup émis en un bloc + 'done'."""
    u, _ = _make_collab(db, "coach7@bmci.local")
    db.commit()

    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(cs, "chat_stream", boom)
    monkeypatch.setattr(cs, "generate", lambda *a, **k: "Repli mono-coup streamé.")
    events = list(cs.chat_agent_stream(db, u.id, "Bonjour", []))

    text = "".join(e["text"] for e in events if e["type"] == "token")
    assert text == "Repli mono-coup streamé."
    assert events[-1]["type"] == "done"


# ---------------------------------------------------- Outils graphe / mobilité


def test_coach_tools_dispatch_alignes():
    """Invariant : chaque schéma d'outil a un handler, et réciproquement."""
    noms = {t["function"]["name"] for t in cs._TOOLS}
    assert {"passerelles_mobilite", "definir_competence"} <= noms
    assert set(cs._DISPATCH) == noms


def test_tool_mobilite_sans_profil(db):
    import json

    out = cs._tool_passerelles_mobilite(db, 999999, {})
    assert "info" in json.loads(out)  # aucun profil -> message, pas d'exception


def test_tool_definir_competence_terme_vide(db):
    import json

    out = cs._tool_definir_competence(db, 1, {})
    assert "info" in json.loads(out)  # terme vide -> message (pas d'appel graphe)
