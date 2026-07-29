#!/usr/bin/env python3
"""
controllers/recommendation_controller.py — Route HTTP des recommandations.

RÔLE
    Expose la recommandation formation & parcours en API REST. Sans logique métier :
    valide l'entrée, délègue au service, renvoie la sortie structurée.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.core.rate_limit import ia_rate_limit
from app.models.user import User
from app.schemas.recommendation import (RecommendationRequest, RecommendationResponse,
                                        RecoJobLaunched, RecoJobStatus)
from app.services import recommendation_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.post("/recommandations", response_model=RecommendationResponse,
             dependencies=[Depends(get_current_user), Depends(ia_rate_limit)],
             summary="Recommander formations & parcours pour un poste visé")
def recommandations(req: RecommendationRequest, db: Session = Depends(get_db)) -> RecommendationResponse:
    """À partir du profil et du poste visé, renvoie les compétences à développer
    (ancrées ESCO/O*NET/SFIA), les passerelles métiers et un plan de développement."""
    return recommendation_service.recommander(
        db, req.profil_competences, req.poste_texte, req.seuil)


@router.get("/ma-reco", response_model=RecommendationResponse,
            dependencies=[Depends(ia_rate_limit)],
            summary="Ma recommandation (profil du compte connecté vs son poste visé)")
def ma_reco(user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> RecommendationResponse:
    """Recommandation pour le collaborateur connecté : ses compétences vs son
    poste visé (aspirations). ⚠️ Utilise Ollama (extraction + reranker + conseil).
    SYNCHRONE (bloque ~85 s au 1er appel) — préférer le mode ASYNCHRONE ci-dessous."""
    return recommendation_service.recommander_pour_user(db, user.id)


@router.post("/ma-reco/async", response_model=RecoJobLaunched, status_code=202,
             dependencies=[Depends(ia_rate_limit)],
             summary="Lancer ma reco en tâche de fond (renvoie un job_id à interroger)")
def lancer_ma_reco(user: User = Depends(get_current_user)) -> RecoJobLaunched:
    """Non-bloquant : démarre le pipeline Ollama en arrière-plan et renvoie
    immédiatement un `job_id`. Le front interroge ensuite `/ma-reco/jobs/{job_id}`."""
    return RecoJobLaunched(job_id=recommendation_service.launch_reco_job(user.id))


@router.get("/ma-reco/jobs/{job_id}", response_model=RecoJobStatus,
            summary="État de mon job de reco (pending / done + résultat / error)")
def statut_ma_reco(job_id: str, user: User = Depends(get_current_user)) -> RecoJobStatus:
    job = recommendation_service.get_reco_job(job_id, user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job de recommandation introuvable.")
    return RecoJobStatus(**job)
