#!/usr/bin/env python3
"""
services/evaluation_service.py — Score d'ACQUISITION d'une compétence.

MODÈLE (cf. retours tuteur)
    Le % d'acquisition d'une compétence combine plusieurs SOURCES d'évaluation,
    l'évaluation du MANAGER pesant le plus :
        manager 0.70 · mini-jeux 0.20 (futur) · avis des pairs 0.10 (futur).
    Score par source = 1 à 10 → contribue sur 100. Le mélange est renormalisé sur
    les sources RÉELLEMENT présentes.

    Repli DÉMO (continuité) : sans aucune évaluation, on retombe sur le `niveau`
    déclaratif (1-5 → ×20) — c'est la base pré-chargée. Une compétence seulement
    DÉCLARÉE (CV/fiche) sans niveau NI évaluation reste « en attente d'évaluation »
    (acquisition = None) : elle sera scorée quand le manager l'évaluera.

EMPLACEMENT MVC
    Couche "services" : logique métier + persistance des évaluations.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import ProfilCompetence, CompetenceSource
from app.models.offre import Offre
from app.models.user import User
from app.models.competence_evaluation import CompetenceEvaluation, EvaluationSource
from app.models.evaluation_bilan import EvaluationBilan

# Poids par source (manager prépondérant). Renormalisés sur les sources présentes.
WEIGHTS: dict[str, float] = {
    EvaluationSource.MANAGER: 0.70,
    EvaluationSource.JEU: 0.20,
    EvaluationSource.PEER: 0.10,
}


def _blend(scores: dict[str, int]) -> int:
    """Mélange pondéré (renormalisé) des scores 1-10 → pourcentage 0-100."""
    num = sum(WEIGHTS.get(src, 0.0) * sc for src, sc in scores.items())
    den = sum(WEIGHTS.get(src, 0.0) for src in scores)
    if den <= 0:
        return 0
    return max(0, min(100, round((num / den) * 10)))


def acquisition_map(db: Session, profil_id: int) -> dict[int, int | None]:
    """Pour chaque compétence détenue du profil : son % d'acquisition (ou None si
    « en attente d'évaluation »). Requêtes groupées (pas de N+1)."""
    pcs = db.execute(
        select(ProfilCompetence.id, ProfilCompetence.niveau)
        .where(ProfilCompetence.profil_id == profil_id)
    ).all()
    if not pcs:
        return {}
    pc_ids = [pid for (pid, _) in pcs]
    evals = db.execute(
        select(CompetenceEvaluation.profil_competence_id,
               CompetenceEvaluation.source, CompetenceEvaluation.score)
        .where(CompetenceEvaluation.profil_competence_id.in_(pc_ids))
    ).all()
    by_pc: dict[int, dict[str, int]] = {}
    for pc_id, source, score in evals:
        by_pc.setdefault(pc_id, {})[source] = score

    out: dict[int, int | None] = {}
    for pc_id, niveau in pcs:
        scores = by_pc.get(pc_id)
        if scores:
            out[pc_id] = _blend(scores)
        elif niveau is not None:
            out[pc_id] = max(0, min(100, niveau * 20))   # base pré-chargée (démo)
        else:
            out[pc_id] = None                             # en attente d'évaluation
    return out


def evaluer_competence(db: Session, profil_competence_id: int, *, score: int,
                       evaluateur_id: int | None = None,
                       source: str = EvaluationSource.MANAGER,
                       commentaire: str | None = None) -> CompetenceEvaluation | None:
    """Enregistre (upsert) l'évaluation d'une compétence pour une source donnée.
    `score` borné 1-10. None si la compétence n'existe pas."""
    pc = db.get(ProfilCompetence, profil_competence_id)
    if pc is None:
        return None
    score = max(1, min(10, int(score)))
    row = db.scalar(select(CompetenceEvaluation).where(
        CompetenceEvaluation.profil_competence_id == profil_competence_id,
        CompetenceEvaluation.source == source))
    if row is None:
        row = CompetenceEvaluation(profil_competence_id=profil_competence_id, source=source,
                                   score=score, evaluateur_id=evaluateur_id,
                                   commentaire=commentaire)
        db.add(row)
    else:
        row.score = score
        row.evaluateur_id = evaluateur_id
        if commentaire is not None:
            row.commentaire = commentaire
    db.commit()
    db.refresh(row)
    return row


def _trouver_competence(db: Session, profil_id: int, libelle: str,
                        skill_id: int | None) -> ProfilCompetence | None:
    """Compétence détenue du profil correspondant (par skill_id canonique, sinon
    par libellé insensible à la casse)."""
    if skill_id is not None:
        pc = db.scalar(select(ProfilCompetence).where(
            ProfilCompetence.profil_id == profil_id,
            ProfilCompetence.skill_id == skill_id))
        if pc is not None:
            return pc
    lib = (libelle or "").strip().lower()
    if not lib:
        return None
    for pc in db.scalars(select(ProfilCompetence).where(
            ProfilCompetence.profil_id == profil_id)).all():
        if (pc.skill_label_fr or pc.libelle or "").strip().lower() == lib:
            return pc
    return None


def evaluer_mission(db: Session, *, profil_id: int, offre_id: int,
                    evaluateur_id: int | None, items: list[dict]) -> dict:
    """Évaluation de MISSION : le manager note (1-10) les compétences UTILISÉES par
    un participant, au titre d'une offre/mission. Règles (retour tuteur) :
      - une compétence non utilisée n'est pas notée (absente des items) ;
      - une compétence notée mais ABSENTE du profil est AJOUTÉE (source
        evaluation_mission) puis évaluée ;
      - l'évaluation porte l'attribution (évaluateur + offre) pour un affichage
        « évaluée par le manager X dans le cadre de la mission Y ».
    Renvoie {evaluees, ajoutees}."""
    ajoutees = evaluees = 0
    for it in items:
        libelle = (it.get("libelle") or "").strip()
        score_raw = it.get("score")
        if not libelle or score_raw is None:
            continue
        score = max(1, min(10, int(score_raw)))
        skill_id = it.get("skill_id")
        pc = _trouver_competence(db, profil_id, libelle, skill_id)
        if pc is None:
            pc = ProfilCompetence(
                profil_id=profil_id, libelle=libelle,
                skill_id=skill_id, skill_label_fr=(libelle if skill_id else None),
                categorie=it.get("categorie"),
                source=CompetenceSource.EVAL_MISSION,
                acquired_at=datetime.now(timezone.utc))
            db.add(pc)
            db.flush()
            ajoutees += 1
        row = db.scalar(select(CompetenceEvaluation).where(
            CompetenceEvaluation.profil_competence_id == pc.id,
            CompetenceEvaluation.source == EvaluationSource.MANAGER))
        if row is None:
            db.add(CompetenceEvaluation(
                profil_competence_id=pc.id, source=EvaluationSource.MANAGER,
                score=score, evaluateur_id=evaluateur_id, offre_id=offre_id))
        else:
            row.score = score
            row.evaluateur_id = evaluateur_id
            row.offre_id = offre_id
        evaluees += 1
    db.commit()
    return {"evaluees": evaluees, "ajoutees": ajoutees}


def attribution_map(db: Session, profil_id: int) -> dict[int, dict[str, str]]:
    """Pour les compétences évaluées par un manager AU TITRE D'UNE MISSION : renvoie
    {profil_competence_id: {evaluee_par, mission}} pour l'affichage de l'attribution."""
    pc_ids = [r[0] for r in db.execute(
        select(ProfilCompetence.id).where(ProfilCompetence.profil_id == profil_id)).all()]
    if not pc_ids:
        return {}
    rows = db.execute(
        select(CompetenceEvaluation.profil_competence_id,
               CompetenceEvaluation.evaluateur_id, CompetenceEvaluation.offre_id)
        .where(CompetenceEvaluation.profil_competence_id.in_(pc_ids),
               CompetenceEvaluation.source == EvaluationSource.MANAGER,
               CompetenceEvaluation.offre_id.is_not(None))
    ).all()
    if not rows:
        return {}
    user_ids = {r[1] for r in rows if r[1]}
    offre_ids = {r[2] for r in rows if r[2]}
    noms = {u.id: u.name for u in db.scalars(
        select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
    missions = {o.id: o.titre for o in db.scalars(
        select(Offre).where(Offre.id.in_(offre_ids))).all()} if offre_ids else {}
    out: dict[int, dict[str, str]] = {}
    for pc_id, ev_id, off_id in rows:
        out[pc_id] = {
            "evaluee_par": noms.get(ev_id, "le manager"),
            "mission": missions.get(off_id, ""),
        }
    return out


# --- Bilans d'évaluation (journal → « Historique des évaluations ») -----------

def creer_bilan(db: Session, profil_id: int, *, type: str = "mission",
                note: int | None = None, commentaire: str | None = None,
                competences_detectees: int = 0,
                evaluateur_id: int | None = None) -> EvaluationBilan:
    """Enregistre une nouvelle appréciation datée (une ligne d'historique)."""
    bilan = EvaluationBilan(
        profil_id=profil_id, type=type, note=note,
        commentaire=(commentaire or None), competences_detectees=competences_detectees,
        evaluateur_id=evaluateur_id)
    db.add(bilan)
    db.commit()
    db.refresh(bilan)
    return bilan


def list_bilans(db: Session, profil_id: int) -> list[dict]:
    """Historique des bilans d'un profil (plus récent d'abord), nom de l'évaluateur
    résolu. Forme prête à sérialiser en EvaluationBilanOut."""
    bilans = db.scalars(
        select(EvaluationBilan).where(EvaluationBilan.profil_id == profil_id)
        .order_by(EvaluationBilan.created_at.desc(), EvaluationBilan.id.desc())
    ).all()
    if not bilans:
        return []
    user_ids = {b.evaluateur_id for b in bilans if b.evaluateur_id}
    noms = {u.id: u.name for u in db.scalars(
        select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
    return [{
        "id": b.id, "type": b.type, "note": b.note, "commentaire": b.commentaire,
        "competences_detectees": b.competences_detectees,
        "evaluateur_nom": noms.get(b.evaluateur_id),
        "created_at": b.created_at,
    } for b in bilans]
