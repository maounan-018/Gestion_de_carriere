#!/usr/bin/env python3
"""
controllers/redaction_controller.py — Route de l'aide à la rédaction.

RÔLE
    Expose la tâche `redaction` (résumé / reformulation) en API REST.

SÉCURITÉ
    `get_current_user` obligatoire (CSRF vérifié sur le POST). Texte fencé côté service.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.schemas.redaction import RedactionRequest, RedactionResponse
from app.services import redaction_service

router = APIRouter(prefix="/api/redaction", tags=["Rédaction"])


@router.post("", response_model=RedactionResponse,
             dependencies=[Depends(get_current_user)],
             summary="Résumer ou reformuler un texte (bilan, aspiration, note)")
def rediger(req: RedactionRequest) -> RedactionResponse:
    """⚠️ Utilise Ollama (mistral-nemo) : quelques secondes."""
    return RedactionResponse(**redaction_service.rediger(req.texte, req.mode, req.consignes))
