#!/usr/bin/env python3
"""
controllers/skill_matching_controller.py — Route HTTP du matching profil ↔ poste.

RÔLE
    Expose le calcul de correspondance en API REST. Sans logique métier : valide
    l'entrée (schemas), délègue au service, renvoie la sortie structurée.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.core.rate_limit import ia_rate_limit
from app.models.skill import Skill
from app.schemas.skill_matching import MatchRequest, MatchResponse
from app.services import skill_matching_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.get("/rechercher", dependencies=[Depends(get_current_user)],
            summary="Autocomplétion du référentiel de compétences CANONIQUES (sans LLM)")
def rechercher_competences(q: str = Query(..., min_length=2, max_length=120),
                           k: int = Query(8, ge=1, le=20),
                           db: Session = Depends(get_db)) -> list[dict]:
    """Recherche par libellé (LIKE, sans LLM) les compétences canoniques du
    référentiel (ESCO/O*NET/SFIA). Sert au manager pour déclarer des attendus
    ANCRÉS (skill_id) lors de la publication d'une offre/mission/projet."""
    like = f"%{q.strip().lower()}%"
    rows = db.execute(
        select(Skill.id, Skill.label_fr)
        .where(Skill.canonical.is_(True), func.lower(Skill.label_fr).like(like))
        .order_by(func.length(Skill.label_fr))
        .limit(k)
    ).all()
    return [{"skill_id": r[0], "label": r[1]} for r in rows]


@router.post("/matching", response_model=MatchResponse,
             dependencies=[Depends(get_current_user), Depends(ia_rate_limit)],
             summary="Mesurer la correspondance entre un profil et un poste")
def matching_profil_poste(req: MatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    """Calcule le score d'adéquation d'un profil à un poste et détaille les
    compétences couvertes et les écarts (besoins de formation)."""
    return skill_matching_service.match_profile_to_job(
        db, req.profil_competences, req.poste_texte, req.seuil)
