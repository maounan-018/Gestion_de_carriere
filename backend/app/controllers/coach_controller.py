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
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.auth.dependencies import get_current_user
from app.core.rate_limit import ia_rate_limit
from app.models.user import User
from app.schemas.coach import CoachRequest, CoachResponse
from app.services import coach_service

router = APIRouter(prefix="/api/coach", tags=["Coach"])


@router.post("", response_model=CoachResponse,
             dependencies=[Depends(ia_rate_limit)],
             summary="Dialoguer avec mon Coach Carrière (contextualisé sur mon profil)")
def coach(req: CoachRequest, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)) -> CoachResponse:
    """⚠️ Utilise Ollama (mistral-nemo) : quelques secondes par réponse."""
    return CoachResponse(**coach_service.chat_agent(db, user.id, req.message, req.history))


@router.post("/stream", dependencies=[Depends(ia_rate_limit)],
             summary="Dialoguer avec mon Coach Carrière (réponse en streaming SSE)")
def coach_stream(req: CoachRequest, user: User = Depends(get_current_user)) -> EventSourceResponse:
    """Même coach agentique, mais la réponse arrive en flux (Server-Sent Events).

    SSE natif FastAPI (`EventSourceResponse`) : keep-alive périodique, Cache-Control
    et X-Accel-Buffering (anti-buffering proxy) gérés AUTOMATIQUEMENT. Chaque
    événement est un `ServerSentEvent(data=…)` (encodé JSON dans le champ `data:`) :
    `{"type":"tool",…}` (donnée interrogée), `{"type":"token","text":…}` (fragment),
    `{"type":"reset"}`, `{"type":"done",…}`. Le front lit via `fetch` (POST+cookie+CSRF).

    Session DB DÉDIÉE au flux : celle de la requête se fermerait avant la fin du
    streaming. On lit `user.id` avant de streamer (l'objet User est lié à la
    session de la dépendance d'auth)."""
    user_id = user.id

    def event_source():
        db = SessionLocal()
        try:
            for ev in coach_service.chat_agent_stream(
                db, user_id, req.message, req.history,
                mode=req.mode, section=req.section, focus=req.focus,
                ouverture=req.ouverture, sujet=req.sujet,
            ):
                yield ServerSentEvent(data=ev)
        finally:
            db.close()

    return EventSourceResponse(event_source())
