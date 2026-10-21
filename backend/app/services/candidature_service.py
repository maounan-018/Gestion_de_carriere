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
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidature import Candidature, CandidatureStatut
from app.models.offre import Offre, OffreCompetence
from app.models.profil import Profil, ProfilCompetence
from app.schemas.candidature import (
    CandidatureCreate,
    CandidatureMineOut,
    CandidatureOut,
    EvaluationOut,
)
from app.services import notification_events

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
        if cur is None or (
            niveau is not None and (cur["niveau"] is None or niveau > cur["niveau"])
        ):
            bucket[key] = {"libelle": comp.libelle, "niveau": niveau}

    for c in detenues:
        if c.skill_id is not None:
            _garder(by_skill, c.skill_id, c)
        for lbl in (_norm(c.libelle), _norm(c.skill_label_fr)):
            if lbl:
                _garder(by_label, lbl, c)
    return by_skill, by_label


# --- Matching SÉMANTIQUE (Bloc B) : repli sur similarité d'embeddings quand
# l'appariement exact (skill_id / libellé) échoue. Ainsi « gestion de la relation
# client » (profil) couvre « relation client » (offre) sans libellé identique.
# Dégradation silencieuse : si le service d'embeddings est indisponible (ex. tests
# hors Ollama), on retombe sur l'appariement exact — le contrat de score est stable.
_SEUIL_SEM = 0.62  # seuil de similarité cosinus pour une couverture
_emb_cache: dict[str, list[float]] = {}


def _cos(a: list[float], b: list[float]) -> float:
    import math

    s = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb) if na and nb else 0.0


def _emb_map(labels: list[str]) -> dict[str, list[float]]:
    """Embeddings (cachés) des libellés normalisés. {} si le service est
    indisponible → repli silencieux sur l'appariement exact."""
    labs = {lab for lab in (_norm(x) for x in labels) if lab}
    missing = [lab for lab in labs if lab not in _emb_cache]
    if missing:
        try:
            from app.services import embedding_service

            for lab, vec in zip(missing, embedding_service.embed_batch(missing), strict=False):
                if vec:
                    _emb_cache[lab] = vec
        except Exception:
            pass
    return {lab: _emb_cache[lab] for lab in labs if lab in _emb_cache}


def _couverture_semantique(
    att: OffreCompetence, emb_map: dict, det_emb: list[tuple]
) -> dict | None:
    """Meilleure compétence détenue sémantiquement proche de l'attendu (cosinus ≥
    seuil), ou None. `det_emb` = [(vecteur, {libelle, niveau})]."""
    a = emb_map.get(_norm(att.libelle)) or emb_map.get(_norm(att.skill_label_fr))
    if a is None or not det_emb:
        return None
    best_s, best_d = 0.0, None
    for vec, d in det_emb:
        s = _cos(a, vec)
        if s > best_s:
            best_s, best_d = s, d
    return best_d if best_s >= _SEUIL_SEM else None


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
        select(OffreCompetence)
        .where(OffreCompetence.offre_id == offre_id)
        .order_by(OffreCompetence.id)
    ).all()
    detenues = db.scalars(
        select(ProfilCompetence).where(ProfilCompetence.profil_id == profil_id)
    ).all()
    by_skill, by_label = _index_detenues(detenues)

    # Bloc B — prépare le repli sémantique (embeddings des deux côtés, cachés).
    # Dégradation silencieuse : emb_map/det_emb vides si le service est indisponible.
    off_labels = [x for att in attendus for x in (att.libelle, att.skill_label_fr)]
    emb_map = _emb_map(list(by_label.keys()) + off_labels)
    det_emb = [(emb_map[lab], data) for lab, data in by_label.items() if lab in emb_map]

    couvertes, ecarts = [], []
    total = 0.0
    acquis = 0.0
    for att in attendus:
        poids = _poids(att.importance)
        total += poids
        base = {
            "competence": att.libelle,
            "importance": att.importance,
            "niveau_requis": att.niveau_requis,
            "skill_id": att.skill_id,
        }
        cov = _trouver_couverture(att, by_skill, by_label)
        semantique = False
        if cov is None:
            cov = _couverture_semantique(att, emb_map, det_emb)
            semantique = cov is not None
        if cov is None:
            ecarts.append({**base, "statut": "manquante"})
        elif (
            att.niveau_requis is not None
            and cov["niveau"] is not None
            and cov["niveau"] < att.niveau_requis
        ):
            # Compétence présente mais niveau insuffisant -> écart (non acquis).
            ecarts.append(
                {
                    **base,
                    "statut": "niveau_insuffisant",
                    "couverte_par": cov["libelle"],
                    "niveau_detenu": cov["niveau"],
                }
            )
        else:
            acquis += poids
            couvertes.append(
                {
                    **base,
                    "statut": "couverte",
                    "couverte_par": cov["libelle"],
                    "niveau_detenu": cov["niveau"],
                    **({"match": "semantique"} if semantique else {}),
                }
            )

    score = round(100 * acquis / total) if total else 100
    return EvaluationOut(
        score=score,
        methode=_METHODE,
        attendus_total=len(attendus),
        couvertes=couvertes,
        ecarts=ecarts,
    )


def _to_out(c: Candidature) -> CandidatureOut:
    out = CandidatureOut.model_validate(c)
    if c.evaluation_json:
        try:
            out.evaluation = EvaluationOut.model_validate(json.loads(c.evaluation_json))
        except Exception:
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
        offre_id=data.offre_id,
        profil_id=data.profil_id,
        statut=CandidatureStatut.DEPOSEE,
        score=evaluation.score,
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


def list_candidatures(
    db: Session,
    *,
    offre_id: int | None = None,
    profil_id: int | None = None,
    statut: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[CandidatureOut]:
    """Liste paginée. Filtrable par offre (candidats d'une offre), par profil
    (candidatures d'un collaborateur) et par statut."""
    stmt = select(Candidature).order_by(
        Candidature.score.desc().nulls_last(), Candidature.id.desc()
    )
    if offre_id is not None:
        stmt = stmt.where(Candidature.offre_id == offre_id)
    if profil_id is not None:
        stmt = stmt.where(Candidature.profil_id == profil_id)
    if statut is not None:
        stmt = stmt.where(Candidature.statut == statut)
    stmt = stmt.limit(min(max(limit, 1), 200)).offset(max(offset, 0))
    return [_to_out(c) for c in db.scalars(stmt).all()]


def decide_candidature(
    db: Session, candidature_id: int, statut: str, decided_by: int | None
) -> CandidatureOut | None:
    """Porte la décision humaine (retenue / rejetee / en_evaluation). None si
    introuvable. Rappel métier : RETENUE est licite même si score < 100 %."""
    c = db.get(Candidature, candidature_id)
    if not c:
        return None
    c.statut = statut
    c.decided_by = decided_by
    c.decided_at = datetime.now(UTC)
    notification_events.on_candidature_decidee(db, c)  # notifie le candidat (atomique)
    db.commit()
    db.refresh(c)
    return _to_out(c)


def retirer_candidature(db: Session, candidature_id: int) -> CandidatureOut | None:
    """Le candidat retire sa candidature → statut `retiree`. None si introuvable.
    (Le contrôle de propriété est fait en amont par `ownership.require_own_candidature`.)"""
    c = db.get(Candidature, candidature_id)
    if not c:
        return None
    c.statut = CandidatureStatut.RETIREE
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
    c.reevaluated_at = datetime.now(UTC)  # trace QUAND le score a été recalculé
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
        CandidatureMineOut(
            id=c.id,
            statut=c.statut,
            score=c.score,
            created_at=c.created_at,
            offre_titre=titre,
            offre_type=typ,
        )
        for (c, titre, typ) in rows
    ]


def list_mine_for_user(db: Session, user_id: int) -> list[CandidatureMineOut]:
    """Mes candidatures pour le profil LIÉ au compte connecté (vide si sans profil)."""
    p = db.scalar(select(Profil).where(Profil.user_id == user_id))
    return list_mine(db, p.id) if p else []
