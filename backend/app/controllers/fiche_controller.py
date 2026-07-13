#!/usr/bin/env python3
"""
controllers/fiche_controller.py — Routes HTTP de la fiche de poste (gabarit + extraction).

RÔLE
    Expose : (1) le GABARIT de fiche (typologie éditable) pour l'afficher/l'éditer ;
    (2) l'EXTRACTION de compétences d'une fiche structurée. Fin, sans logique métier :
    délègue aux services. (L'édition du gabarit et l'extraction seront protégées par
    RBAC quand l'auth sera branchée.)

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.fiche_extraction import FicheRequest, FicheResponse, GabaritResponse
from app.services import fiche_config_service, fiche_extraction_service

router = APIRouter(prefix="/api/fiches", tags=["Fiches de poste"])


@router.get("/gabarit", response_model=GabaritResponse,
            summary="Obtenir le gabarit (typologie) de fiche de poste")
def obtenir_gabarit() -> GabaritResponse:
    """Renvoie la typologie éditable de la fiche (rubriques + traitement de chacune)."""
    try:
        return fiche_config_service.load_schema()
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=f"Gabarit invalide : {e}")


@router.post("/extraction", response_model=FicheResponse,
             summary="Extraire les compétences d'une fiche de poste structurée")
def extraire_fiche(req: FicheRequest, db: Session = Depends(get_db)) -> FicheResponse:
    """À partir des rubriques d'une fiche (selon le gabarit), extrait les métadonnées
    du poste + les compétences typées ancrées au graphe + langues + indicateurs."""
    return fiche_extraction_service.extract_from_fiche(db, req.sections, req.top_k)
