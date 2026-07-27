#!/usr/bin/env python3
"""
services/candidature_service.py — Logique métier d'une Candidature (profil ↔ offre).

RÔLE
    Dépose une candidature d'un Profil à une Offre et l'ÉVALUE : confronte les
    compétences DÉTENUES (ProfilCompetence) aux ATTENDUS de l'offre
    (OffreCompetence) → `score` pondéré (essentielle > souhaitée) + snapshot des
    couvertes/écarts (traçabilité, persisté dans `evaluation_json`).

    ⚠️ RÈGLE MÉTIER : le score est INDICATIF, jamais un filtre. Un candidat < 100 %
    peut être RETENU — `decide_candidature` porte la décision humaine.

    MATCHING (Bloc A) : appariement ENTITÉ-À-ENTITÉ déterministe (skill_id ancré au
    graphe, sinon libellé normalisé) + contrôle de niveau. Volontairement simple et
    traçable. Le Bloc B l'enrichira d'un matching sémantique (reranker bge + graphe)
    sur ces mêmes entités persistées, sans changer ce contrat.

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidature import Candidature, CandidatureStatut
from app.models.offre import Offre, OffreCompetence
from app.models.profil import Profil, ProfilCompetence
from app.schemas.candidature import (CandidatureCreate, CandidatureOut, EvaluationOut,
                                     CandidatureMineOut)

_METHODE = "entites_v1"  # appariement déterministe skill_id/libellé (cf. docstring)


def _poids(importance: str | None) -> float:
    """Pondération d'un attendu : essentielle=1.0, souhaitée/autre=0.5."""
    return 1.0 if str(importance or "").lower().startswith("essent") else 0.5


def _norm(txt: str | None) -> str | None:
    return txt.strip().lower() if txt and txt.strip() else None


def _index_detenues(detenues: list[ProfilCompetence]) -> tuple[dict, dict]:
    """Indexe les compétences détenues par skill_id et par libellé normalisé,
    en gardant le meilleur niveau connu et un libellé représentatif."""
    by_skill: dict[int, dict] = {}
    by_label: dict[str, dict] = {}

    def _garder(bucket: dict, key, comp: ProfilCompetence):
        cur = bucket.get(key)
        niveau = comp.niveau
        if cur is None or (niveau is not None and (cur["niveau"] is None or niveau > cur["niveau"])):
            bucket[key] = {"libelle": comp.libelle, "niveau": niveau}

    for c in detenues:
        if c.skill_id is not None:
            _garder(by_skill, c.skill_id, c)
        for lbl in (_norm(c.libelle), _norm(c.skill_label_fr)):
            if lbl:
                _garder(by_label, lbl, c)
    return by_skill, by_label


def _trouver_couverture(att: OffreCompetence, by_skill: dict, by_label: dict) -> dict | None:
    """Cherche une compétence détenue couvrant l'attendu (skill_id prioritaire,
    puis libellé normalisé). Renvoie {libelle, niveau} ou None."""
    if att.skill_id is not None and att.skill_id in by_skill:
        return by_skill[att.skill_id]
    for lbl in (_norm(att.libelle), _norm(att.skill_label_fr)):
        if lbl and lbl in by_label:
            return by_label[lbl]
    return None


def evaluer(db: Session, offre_id: int, profil_id: int) -> EvaluationOut:
    """Évalue un profil contre les attendus d'une offre (score + snapshot).
    Score = 100 × Σ poids(couvertes) / Σ poids(attendus). Aucun attendu → 100."""
    attendus = db.scalars(
        select(OffreCompetence).where(OffreCompetence.offre_id == offre_id)
        .order_by(OffreCompetence.id)
    ).all()
    detenues = db.scalars(
        select(ProfilCompetence).where(ProfilCompetence.profil_id == profil_id)
    ).all()
    by_skill, by_label = _index_detenues(detenues)

    couvertes, ecarts = [], []
    total = 0.0
    acquis = 0.0
    for att in attendus:
        poids = _poids(att.importance)
        total += poids
        base = {"competence": att.libelle, "importance": att.importance,
                "niveau_requis": att.niveau_requis, "skill_id": att.skill_id}
        cov = _trouver_couverture(att, by_skill, by_label)
        if cov is None:
            ecarts.append({**base, "statut": "manquante"})
        elif (att.niveau_requis is not None and cov["niveau"] is not None
              and cov["niveau"] < att.niveau_requis):
            # Compétence présente mais niveau insuffisant -> écart (non acquis).
            ecarts.append({**base, "statut": "niveau_insuffisant",
                           "couverte_par": cov["libelle"], "niveau_detenu": cov["niveau"]})
        else:
            acquis += poids
            couvertes.append({**base, "statut": "couverte",
                              "couverte_par": cov["libelle"], "niveau_detenu": cov["niveau"]})

    score = round(100 * acquis / total) if total else 100
    return EvaluationOut(score=score, methode=_METHODE, attendus_total=len(attendus),
                         couvertes=couvertes, ecarts=ecarts)


def _to_out(c: Candidature) -> CandidatureOut:
    out = CandidatureOut.model_validate(c)
    if c.evaluation_json:
        try:
            out.evaluation = EvaluationOut.model_validate(json.loads(c.evaluation_json))
        except Exception:  # noqa: BLE001 — snapshot illisible : on renvoie la candidature sans détail
            out.evaluation = None
    return out


def create_candidature(db: Session, data: CandidatureCreate) -> CandidatureOut:
    """Dépose et évalue une candidature. Lève ValueError si l'offre ou le profil
    est introuvable, ou si le profil a déjà candidaté à cette offre (unicité)."""
    if db.get(Offre, data.offre_id) is None:
        raise ValueError(f"Offre {data.offre_id} introuvable.")
    if db.get(Profil, data.profil_id) is None:
        raise ValueError(f"Profil {data.profil_id} introuvable.")

    evaluation = evaluer(db, data.offre_id, data.profil_id)
    c = Candidature(
        offre_id=data.offre_id, profil_id=data.profil_id,
        statut=CandidatureStatut.DEPOSEE, score=evaluation.score,
        evaluation_json=evaluation.model_dump_json(),
        motivation=data.motivation,
    )
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Ce profil a déjà candidaté à cette offre.")
    db.refresh(c)
    return _to_out(c)


def get_candidature(db: Session, candidature_id: int) -> CandidatureOut | None:
    c = db.get(Candidature, candidature_id)
    return _to_out(c) if c else None


def list_candidatures(db: Session, *, offre_id: int | None = None,
                      profil_id: int | None = None, statut: str | None = None,
                      limit: int = 50, offset: int = 0) -> list[CandidatureOut]:
    """Liste paginée. Filtrable par offre (candidats d'une offre), par profil
    (candidatures d'un collaborateur) et par statut."""
    stmt = select(Candidature).order_by(Candidature.score.desc().nulls_last(),
                                        Candidature.id.desc())
    if offre_id is not None:
        stmt = stmt.where(Candidature.offre_id == offre_id)
    if profil_id is not None:
        stmt = stmt.where(Candidature.profil_id == profil_id)
    if statut is not None:
        stmt = stmt.where(Candidature.statut == statut)
    stmt = stmt.limit(min(max(limit, 1), 200)).offset(max(offset, 0))
    return [_to_out(c) for c in db.scalars(stmt).all()]


def decide_candidature(db: Session, candidature_id: int, statut: str,
                       decided_by: int | None) -> CandidatureOut | None:
    """Porte la décision humaine (retenue / rejetee / en_evaluation). None si
    introuvable. Rappel métier : RETENUE est licite même si score < 100 %."""
    c = db.get(Candidature, candidature_id)
    if not c:
        return None
    c.statut = statut
    c.decided_by = decided_by
    c.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(c)
    return _to_out(c)


def reevaluer_candidature(db: Session, candidature_id: int) -> CandidatureOut | None:
    """Recalcule le score/snapshot (ex : attendus de l'offre modifiés depuis le
    dépôt). None si introuvable. Ne change PAS le statut/la décision."""
    c = db.get(Candidature, candidature_id)
    if not c:
        return None
    evaluation = evaluer(db, c.offre_id, c.profil_id)
    c.score = evaluation.score
    c.evaluation_json = evaluation.model_dump_json()
    c.reevaluated_at = datetime.now(timezone.utc)  # trace QUAND le score a été recalculé
    db.commit()
    db.refresh(c)
    return _to_out(c)


def list_mine(db: Session, profil_id: int) -> list[CandidatureMineOut]:
    """« Mes candidatures » : candidatures d'un profil + titre/type de l'offre
    (jointure), triées de la plus récente à la plus ancienne."""
    rows = db.execute(
        select(Candidature, Offre.titre, Offre.type)
        .join(Offre, Offre.id == Candidature.offre_id)
        .where(Candidature.profil_id == profil_id)
        .order_by(Candidature.created_at.desc())
    ).all()
    return [
        CandidatureMineOut(id=c.id, statut=c.statut, score=c.score,
                           created_at=c.created_at, offre_titre=titre, offre_type=typ)
        for (c, titre, typ) in rows
    ]


def list_mine_for_user(db: Session, user_id: int) -> list[CandidatureMineOut]:
    """Mes candidatures pour le profil LIÉ au compte connecté (vide si sans profil)."""
    p = db.scalar(select(Profil).where(Profil.user_id == user_id))
    return list_mine(db, p.id) if p else []
