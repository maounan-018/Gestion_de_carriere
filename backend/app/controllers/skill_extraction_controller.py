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
from app.core.rate_limit import ia_rate_limit
from app.schemas.skill_extraction import ExtractRequest, ExtractResponse
from app.schemas.normalisation import NormaliseRequest, NormaliseResponse
from app.services import skill_extraction_service, normalisation_service

router = APIRouter(prefix="/api/competences", tags=["Compétences"])


@router.post("/extraction", response_model=ExtractResponse,
             dependencies=[Depends(get_current_user), Depends(ia_rate_limit)],
             summary="Extraire les compétences d'un descriptif de poste")
def extraire_competences(req: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    """Extrait les compétences d'un descriptif de poste et les ancre dans le graphe
    (compétences canoniques ESCO/O*NET). Sortie réexploitable par le matching."""
    return skill_extraction_service.extract_skills(db, req.text, req.top_k)


@router.post("/normaliser", response_model=NormaliseResponse,
             dependencies=[Depends(get_current_user), Depends(ia_rate_limit)],
             summary="Normaliser / regrouper des libellés de compétences (forme canonique)")
def normaliser_competences(req: NormaliseRequest) -> NormaliseResponse:
    """Canonicalise une liste de libellés (dédup casse/synonymes/franglais) en
    groupes. Utile pour nettoyer des compétences avant stockage ou matching."""
    return NormaliseResponse(**normalisation_service.normaliser(req.libelles))
