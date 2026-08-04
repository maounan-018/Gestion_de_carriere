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

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user, client_ip
from app.core.rate_limit import ia_rate_limit
from app.models.user import Role, User
from app.models.fiche import Fiche, FicheCompetence
from app.models.audit_log import AuditEventType
from app.schemas.fiche_extraction import (FicheRequest, FicheResponse, GabaritResponse,
                                          DepartementInfo, CartographieDoc,
                                          FicheGenerationRequest, FicheGeneree)
from app.schemas.fiche import FicheListItem, FicheDetailOut, FicheCompetenceOut
from app.services import (fiche_config_service, fiche_extraction_service,
                          fiche_generation_service, cartography_service, audit_service)

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


@router.put("/gabarit", response_model=GabaritResponse,
            summary="Éditer le gabarit de fiche (RH/ADMIN) — validé, persisté, audité")
def enregistrer_gabarit(gabarit: GabaritResponse, request: Request,
                        user: User = Depends(require_roles(Role.RH, Role.ADMIN))) -> GabaritResponse:
    """Remplace le gabarit. Validé AVANT écriture (un gabarit cassé -> 400, fichier
    intact). Persistance atomique + rechargée à chaud par l'extraction."""
    try:
        saved = fiche_config_service.save_schema(gabarit.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.log_event(
        AuditEventType.CONFIG_CHANGED,
        f"Gabarit de fiche modifié ({len(saved.get('sections', []))} sections)",
        user_id=user.id, username=user.email, role=user.role,
        ip_address=client_ip(request), endpoint=request.url.path, http_method=request.method)
    return GabaritResponse(**saved)


@router.get("/cartographie", response_model=CartographieDoc,
            dependencies=[Depends(get_current_user)],
            summary="Cartographie complète départements→métiers (pour l'éditeur)")
def obtenir_cartographie() -> CartographieDoc:
    try:
        return CartographieDoc(**cartography_service.load())
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=f"Cartographie invalide : {e}")


@router.put("/cartographie", response_model=CartographieDoc,
            summary="Éditer la cartographie départements→métiers (RH/ADMIN) — validé, persisté, audité")
def enregistrer_cartographie(carto: CartographieDoc, request: Request,
                             user: User = Depends(require_roles(Role.RH, Role.ADMIN))) -> CartographieDoc:
    """Remplace la cartographie. Validée AVANT écriture (-> 400 si cassée, fichier
    intact). Persistance atomique, rechargée à chaud par la génération de fiches."""
    try:
        saved = cartography_service.save(carto.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit_service.log_event(
        AuditEventType.CONFIG_CHANGED,
        f"Cartographie modifiée ({len(saved.get('departements', []))} départements)",
        user_id=user.id, username=user.email, role=user.role,
        ip_address=client_ip(request), endpoint=request.url.path, http_method=request.method)
    return CartographieDoc(**saved)


@router.post("/extraction", response_model=FicheResponse,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN)), Depends(ia_rate_limit)],
             summary="Extraire les compétences d'une fiche de poste structurée")
def extraire_fiche(req: FicheRequest, db: Session = Depends(get_db)) -> FicheResponse:
    """À partir des rubriques d'une fiche (selon le gabarit), extrait les métadonnées
    du poste + les compétences typées ancrées au graphe + langues + indicateurs."""
    return fiche_extraction_service.extract_from_fiche(db, req.sections, req.top_k)


@router.get("", response_model=list[FicheListItem],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN, Role.MANAGER))],
            summary="Lister les fiches de poste (sélecteur « Publier une offre »)")
def lister_fiches(departement_key: str | None = Query(None),
                  q: str | None = Query(None, description="Filtre sur l'intitulé du poste."),
                  db: Session = Depends(get_db)) -> list[Fiche]:
    stmt = select(Fiche).order_by(Fiche.intitule_poste)
    if departement_key:
        stmt = stmt.where(Fiche.departement_key == departement_key)
    if q:
        stmt = stmt.where(Fiche.intitule_poste.ilike(f"%{q}%"))
    return list(db.scalars(stmt.limit(300)).all())


@router.get("/{fiche_id}", response_model=FicheDetailOut,
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN, Role.MANAGER))],
            summary="Détail d'une fiche de poste (mission, activités, compétences attendues)")
def detail_fiche(fiche_id: int, db: Session = Depends(get_db)) -> FicheDetailOut:
    f = db.get(Fiche, fiche_id)
    if f is None:
        raise HTTPException(status_code=404, detail="Fiche introuvable.")
    comps = db.scalars(
        select(FicheCompetence).where(FicheCompetence.fiche_id == fiche_id)
        .order_by(FicheCompetence.id)).all()
    return FicheDetailOut(
        id=f.id, intitule_poste=f.intitule_poste, departement_key=f.departement_key,
        perimetre_bmci=f.perimetre_bmci, famille_metier=f.famille_metier,
        mission=f.mission, activites_principales=f.activites_principales,
        langues=f.langues, indicateurs_performances=f.indicateurs_performances,
        competences=[FicheCompetenceOut.model_validate(c) for c in comps])
