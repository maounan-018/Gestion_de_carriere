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

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import ProfilCompetence
from app.models.competence_evaluation import CompetenceEvaluation, EvaluationSource

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
