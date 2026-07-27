#!/usr/bin/env python3
"""
controllers/recommendation_controller.py — Route HTTP des recommandations.

RÔLE
    Expose la recommandation formation & parcours en API REST. Sans logique métier :
    valide l'entrée, délègue au service, renvoie la sortie structurée.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services import recommendation_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.post("/recommandations", response_model=RecommendationResponse,
             dependencies=[Depends(get_current_user)],
             summary="Recommander formations & parcours pour un poste visé")
def recommandations(req: RecommendationRequest, db: Session = Depends(get_db)) -> RecommendationResponse:
    """À partir du profil et du poste visé, renvoie les compétences à développer
    (ancrées ESCO/O*NET/SFIA), les passerelles métiers et un plan de développement."""
    return recommendation_service.recommander(
        db, req.profil_competences, req.poste_texte, req.seuil)
