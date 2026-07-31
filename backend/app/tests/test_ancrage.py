#!/usr/bin/env python3
"""
tests/test_ancrage.py — Backfill d'ancrage des compétences détenues au graphe.
Sans Ollama : `search_skills` monkeypatché.
"""

from app.services import profil_service as ps
from app.models.user import User, Role
from app.models.profil import Profil, ProfilCompetence
from app.tests.conftest import auth, hdr


def _profil_avec_competence(db, email, libelle):
    u = User(email=email, name="Anc", role=Role.COLLAB)
    db.add(u)
    db.flush()
    p = Profil(user_id=u.id, nom="X", synthetique=True)
    db.add(p)
    db.flush()
    pc = ProfilCompetence(profil_id=p.id, libelle=libelle)   # source declaratif par défaut
    db.add(pc)
    db.commit()
    return pc


def test_ancre_si_match_confiant(db, monkeypatch):
    from app.services import skill_search_service
    pc = _profil_avec_competence(db, "anc1@bmci.local", "Gestion des talents")
    monkeypatch.setattr(skill_search_service, "search_skills",
                        lambda db, q, k=1: [{"skill_id": 42, "label_fr": "gestion des talents",
                                             "skill_type": "knowledge", "rerank_score": 0.9}])
    res = ps.ancrer_competences_detenues(db)
    assert res["ancrees"] == 1 and res["categorisees"] == 1
    assert pc.skill_id == 42 and pc.skill_label_fr == "gestion des talents"
    assert pc.categorie == "metier"          # knowledge -> metier


def test_gate_rejette_ancrage_faible(db, monkeypatch):
    from app.services import skill_search_service
    pc = _profil_avec_competence(db, "anc2@bmci.local", "truc vague")
    monkeypatch.setattr(skill_search_service, "search_skills",
                        lambda db, q, k=1: [{"skill_id": 7, "label_fr": "hors sujet",
                                             "skill_type": "skill", "rerank_score": 0.05}])
    res = ps.ancrer_competences_detenues(db)
    assert res["ancrees"] == 0 and pc.skill_id is None       # gate : pas de faux ancrage


def test_type_skill_ne_force_pas_la_categorie(db, monkeypatch):
    from app.services import skill_search_service
    pc = _profil_avec_competence(db, "anc3@bmci.local", "Management d'équipe")
    monkeypatch.setattr(skill_search_service, "search_skills",
                        lambda db, q, k=1: [{"skill_id": 9, "label_fr": "diriger une équipe",
                                             "skill_type": "skill", "rerank_score": 0.8}])
    res = ps.ancrer_competences_detenues(db)
    assert res["ancrees"] == 1 and pc.skill_id == 9
    assert res["categorisees"] == 0 and pc.categorie is None  # 'skill' -> pas de famille forcée


def test_endpoint_reserve_aux_rh(client, monkeypatch):
    from app.services import profil_service
    monkeypatch.setattr(profil_service, "ancrer_competences_detenues",
                        lambda db, **k: {"examinees": 45, "ancrees": 40, "categorisees": 12})
    csrf = auth(client, "rh")
    r = client.post("/api/profils/ancrer-competences", headers=hdr(csrf))
    assert r.status_code == 200, r.text
    assert r.json()["ancrees"] == 40

    csrf2 = auth(client, "collab")
    r2 = client.post("/api/profils/ancrer-competences", headers=hdr(csrf2))
    assert r2.status_code == 403
