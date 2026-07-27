#!/usr/bin/env python3
"""
controllers/skill_extraction_controller.py — Route HTTP de l'extraction de compétences.

RÔLE
    Expose la fonctionnalité "extraction de compétences" en API REST. Fin et sans
    logique métier : valide l'entrée (schemas), délègue au service, renvoie la
    sortie structurée. Un contrôleur = une fonctionnalité (convention MVC).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.schemas.skill_extraction import ExtractRequest, ExtractResponse
from app.services import skill_extraction_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.post("/extraction", response_model=ExtractResponse,
             dependencies=[Depends(get_current_user)],
             summary="Extraire les compétences d'un descriptif de poste")
def extraire_competences(req: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    """Extrait les compétences d'un descriptif de poste et les ancre dans le graphe
    (compétences canoniques ESCO/O*NET). Sortie réexploitable par le matching."""
    return skill_extraction_service.extract_skills(db, req.text, req.top_k)
