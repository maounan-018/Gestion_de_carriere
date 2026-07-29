#!/usr/bin/env python3
"""
controllers/fiche_controller.py — Routes HTTP de la fiche de poste (gabarit + extraction).

RÔLE
    Expose : (1) le GABARIT de fiche (typologie éditable) pour l'afficher/l'éditer ;
    (2) l'EXTRACTION de compétences d'une fiche structurée. Fin, sans logique métier :
    délègue aux services.

SÉCURITÉ (RBAC branché — Bloc C)
    Génération et extraction (outils RH/administration) réservées à RH/ADMIN ;
    cartographie et gabarit (référentiels) ouverts à tout utilisateur authentifié.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.core.rate_limit import ia_rate_limit
from app.models.user import Role
from app.schemas.fiche_extraction import (FicheRequest, FicheResponse, GabaritResponse,
                                          DepartementInfo, FicheGenerationRequest, FicheGeneree)
from app.services import (fiche_config_service, fiche_extraction_service,
                          fiche_generation_service, cartography_service)

router = APIRouter(prefix="/api/fiches", tags=["Fiches de poste"])


@router.get("/departements", response_model=list[DepartementInfo],
            dependencies=[Depends(get_current_user)],
            summary="Lister la cartographie départements → métiers")
def lister_departements() -> list[dict]:
    """Renvoie la cartographie BMCI (départements, pôles, métiers-types)."""
    return cartography_service.departements()


@router.post("/generation", response_model=FicheGeneree,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN)), Depends(ia_rate_limit)],
             summary="Générer une fiche de poste (compétences inférées, SYNTHÉTIQUE)")
def generer_fiche(req: FicheGenerationRequest, db: Session = Depends(get_db)) -> FicheGeneree:
    """Génère une fiche de poste pour un métier d'un département (compétences inférées
    depuis le graphe + rédaction FR). Contenu SYNTHÉTIQUE (jamais des données réelles)."""
    dept = cartography_service.get_departement(req.departement_key)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Département inconnu : {req.departement_key}")
    return fiche_generation_service.generate_fiche(db, req.metier, dept)


@router.get("/gabarit", response_model=GabaritResponse,
            dependencies=[Depends(get_current_user)],
            summary="Obtenir le gabarit (typologie) de fiche de poste")
def obtenir_gabarit() -> GabaritResponse:
    """Renvoie la typologie éditable de la fiche (rubriques + traitement de chacune)."""
    try:
        return fiche_config_service.load_schema()
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=f"Gabarit invalide : {e}")


@router.post("/extraction", response_model=FicheResponse,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN)), Depends(ia_rate_limit)],
             summary="Extraire les compétences d'une fiche de poste structurée")
def extraire_fiche(req: FicheRequest, db: Session = Depends(get_db)) -> FicheResponse:
    """À partir des rubriques d'une fiche (selon le gabarit), extrait les métadonnées
    du poste + les compétences typées ancrées au graphe + langues + indicateurs."""
    return fiche_extraction_service.extract_from_fiche(db, req.sections, req.top_k)
