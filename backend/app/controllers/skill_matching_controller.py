#!/usr/bin/env python3
"""
controllers/skill_matching_controller.py — Route HTTP du matching profil ↔ poste.

RÔLE
    Expose le calcul de correspondance en API REST. Sans logique métier : valide
    l'entrée (schemas), délègue au service, renvoie la sortie structurée.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.skill_matching import MatchRequest, MatchResponse
from app.services import skill_matching_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.post("/matching", response_model=MatchResponse,
             summary="Mesurer la correspondance entre un profil et un poste")
def matching_profil_poste(req: MatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    """Calcule le score d'adéquation d'un profil à un poste et détaille les
    compétences couvertes et les écarts (besoins de formation)."""
    return skill_matching_service.match_profile_to_job(
        db, req.profil_competences, req.poste_texte, req.seuil)
