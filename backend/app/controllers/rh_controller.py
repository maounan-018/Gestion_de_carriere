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
from app.core.rate_limit import ia_rate_limit
from app.models.user import Role
from app.schemas.dashboard import VeilleItem, AlerteItem
from app.schemas.succession import SuccessionRequest, SuccessionResponse
from app.services import dashboard_service, succession_service

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


@router.post("/succession", response_model=SuccessionResponse,
             dependencies=[Depends(ia_rate_limit)],
             summary="Plan de succession raisonné d'un pôle (IA de raisonnement lourde)")
def succession(req: SuccessionRequest, db: Session = Depends(get_db)) -> SuccessionResponse:
    """⚠️ Tâche BATCH : modèle de raisonnement 23 Go (qwen3.6) — lent sur 8 Go VRAM.
    Analyse la cartographie réelle du pôle et propose successeurs/écarts/risques."""
    return SuccessionResponse(**succession_service.plan_succession(db, req.departement_key))
