#!/usr/bin/env python3
"""
controllers/dashboard_controller.py — Tableaux de bord & agrégations RH / manager.

RÔLE
    Expose les indicateurs et cartographies calculés par `dashboard_service`.

SÉCURITÉ (RBAC)
    - KPIs : RH/ADMIN (scope rh) ou MANAGER (scope manager, borné à son équipe).
    - Cartographie & hauts potentiels : RH/ADMIN (vue globale de la banque).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.models.user import User, Role
from app.schemas.dashboard import (DashboardKpis, CartoMatrix, FamilleCompetence,
                                    HautPotentielItem, SyntheseRh)
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboards", tags=["Tableaux de bord"])


@router.get("/kpis", response_model=DashboardKpis,
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN, Role.MANAGER))],
            summary="Indicateurs clés (scope RH global ou manager/équipe)")
def kpis(scope: str = Query("rh", pattern="^(rh|manager)$"),
         user: User = Depends(get_current_user),
         db: Session = Depends(get_db)) -> DashboardKpis:
    if scope == "manager":
        if user.role not in (Role.MANAGER, Role.RH, Role.ADMIN):
            raise HTTPException(status_code=403, detail="Droits insuffisants.")
        return DashboardKpis(scope="manager", kpis=dashboard_service.kpis_manager(db, user.id))
    # scope rh : réservé RH/ADMIN
    if user.role not in (Role.RH, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Vue RH réservée.")
    return DashboardKpis(scope="rh", kpis=dashboard_service.kpis_rh(db))


@router.get("/cartographie", response_model=CartoMatrix,
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Cartographie des compétences par département")
def cartographie(db: Session = Depends(get_db)) -> CartoMatrix:
    return dashboard_service.cartographie(db)


@router.get("/equipe/cartographie", response_model=CartoMatrix,
            dependencies=[Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN))],
            summary="Cartographie des compétences de MON équipe (même nomenclature que la carto RH)")
def cartographie_equipe(user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> CartoMatrix:
    """Lignes = collaborateurs de l'équipe du manager connecté ; colonnes = familles
    (mêmes que la cartographie RH). Cellule = niveau moyen du membre par famille."""
    return dashboard_service.cartographie_equipe(db, user.id)


@router.get("/synthese", response_model=SyntheseRh,
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Synthèse RH consolidée (effectifs par pôle, pipeline candidatures, familles en tension)")
def synthese(db: Session = Depends(get_db)) -> SyntheseRh:
    return SyntheseRh(**dashboard_service.synthese(db))


@router.get("/familles", response_model=list[FamilleCompetence],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Cartographie par famille de compétences (couverture interne vs demande, tensions)")
def familles(db: Session = Depends(get_db)) -> list[FamilleCompetence]:
    return dashboard_service.familles(db)


@router.get("/hauts-potentiels", response_model=list[HautPotentielItem],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Hauts potentiels (proxy : niveau moyen de compétences)")
def hauts_potentiels(limit: int = Query(10, ge=1, le=50),
                     db: Session = Depends(get_db)) -> list[HautPotentielItem]:
    return dashboard_service.hauts_potentiels(db, limit=limit)
