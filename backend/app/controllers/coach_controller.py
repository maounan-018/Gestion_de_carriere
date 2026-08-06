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

import json

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse
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
def coach_stream(req: CoachRequest, user: User = Depends(get_current_user)) -> StreamingResponse:
    """Même coach agentique, mais la réponse arrive en flux (Server-Sent Events).

    SSE via `StreamingResponse` : chaque événement est une trame `data: <json>\\n\\n`.
    Payloads : `{"type":"tool",…}` (donnée interrogée), `{"type":"token","text":…}`
    (fragment), `{"type":"reset"}`, `{"type":"done",…}`. Le front lit via `fetch`
    (POST+cookie+CSRF) en découpant sur les lignes vides.

    ⚠️ On formate les trames SSE À LA MAIN plutôt que via `fastapi.sse.EventSourceResponse` :
    dans FastAPI 0.139 cette classe n'est qu'un MARQUEUR (l'encodage des ServerSentEvent
    se fait dans la couche routage, seulement avec `response_class=…`) — la construire
    directement laissait passer des objets bruts que Starlette tentait d'`encode()`
    (AttributeError → 500). Cette voie est robuste et indépendante des versions.

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
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        event_source(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"})
