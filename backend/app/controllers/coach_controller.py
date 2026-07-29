#!/usr/bin/env python3
"""
controllers/coach_controller.py — Route du Coach Carrière.

RÔLE
    Expose le chat du coach. Le coach répond sur le profil du compte CONNECTÉ.

SÉCURITÉ
    `get_current_user` obligatoire (CSRF vérifié sur ce POST). Le coach n'accède
    qu'au profil de l'utilisateur authentifié — aucun accès aux données d'autrui.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.coach import CoachRequest, CoachResponse
from app.services import coach_service

router = APIRouter(prefix="/api/coach", tags=["Coach"])


@router.post("", response_model=CoachResponse,
             summary="Dialoguer avec mon Coach Carrière (contextualisé sur mon profil)")
def coach(req: CoachRequest, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)) -> CoachResponse:
    """⚠️ Utilise Ollama (mistral-nemo) : quelques secondes par réponse."""
    return CoachResponse(**coach_service.chat(db, user.id, req.message, req.history))
