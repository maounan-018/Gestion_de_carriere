#!/usr/bin/env python3
"""
controllers/rh_controller.py — Vues analytiques RH (veille & alertes).

RÔLE
    Expose la veille des entretiens et les alertes RH dérivées de signaux réels,
    calculées par `dashboard_service`.

SÉCURITÉ (RBAC)
    Réservé RH/ADMIN (vue globale de la banque).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles
from app.models.user import Role
from app.schemas.dashboard import VeilleItem, AlerteItem
from app.services import dashboard_service

router = APIRouter(prefix="/api/rh", tags=["RH"],
                   dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))])


@router.get("/veille", response_model=list[VeilleItem],
            summary="Veille des entretiens (réalisés / planifiés / en retard)")
def veille(db: Session = Depends(get_db)) -> list[VeilleItem]:
    return dashboard_service.veille(db)


@router.get("/alertes", response_model=list[AlerteItem],
            summary="Alertes RH dérivées (potentiels, entretiens en retard, mobilité)")
def alertes(db: Session = Depends(get_db)) -> list[AlerteItem]:
    return dashboard_service.alertes(db)
