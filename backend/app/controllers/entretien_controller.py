#!/usr/bin/env python3
"""
controllers/entretien_controller.py — Synthèse de préparation d'entretien (self-service).

RÔLE
    Le collaborateur CONSERVE la synthèse produite au fil de sa simulation de
    préparation d'entretien (sortie IA persistée) et la relit ensuite. Une synthèse
    courante par profil (upsert).

SÉCURITÉ
    Auto-service : lié au compte connecté (get_current_user, CSRF sur POST).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.entretien import SyntheseEntretienIn, SyntheseEntretienOut
from app.services import entretien_service

router = APIRouter(prefix="/api/entretiens", tags=["Entretiens"])


@router.put("/ma-synthese", response_model=SyntheseEntretienOut,
            summary="Conserver la synthèse de MA préparation d'entretien (upsert)")
def enregistrer_ma_synthese(data: SyntheseEntretienIn,
                            user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)) -> SyntheseEntretienOut:
    """Enregistre (ou remplace) la synthèse courante de préparation d'entretien du
    collaborateur. Donnée générée CONSERVÉE (source durable, jamais « live seulement »)."""
    out = entretien_service.enregistrer_ma_synthese(db, user.id, data.synthese)
    if out is None:
        raise HTTPException(status_code=404, detail="Aucun profil lié à ce compte.")
    return SyntheseEntretienOut(**out)


@router.get("/ma-synthese", response_model=SyntheseEntretienOut | None,
            summary="Relire la synthèse persistée de MA préparation d'entretien (null si aucune)")
def charger_ma_synthese(user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> SyntheseEntretienOut | None:
    out = entretien_service.charger_ma_synthese(db, user.id)
    return SyntheseEntretienOut(**out) if out else None
