#!/usr/bin/env python3
"""
controllers/notification_controller.py — Routes des notifications.

RÔLE
    Expose les notifications de l'utilisateur AUTHENTIFIÉ (les siennes uniquement)
    et leur passage en « lu ». Un même endpoint sert les trois espaces (collab /
    manager / RH) : chacun voit ses propres notifications.

SÉCURITÉ
    `get_current_user` obligatoire ; le service filtre par `user.id` → aucun accès
    aux notifications d'autrui. CSRF vérifié sur les méthodes mutantes.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.auth import ownership
from app.models.user import User, Role
from app.schemas.notification import (NotificationOut, MessageRhRequest, MessageRhResult,
                                      MessageProfilRequest, MessageProfilResult)
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/message-rh", response_model=MessageRhResult,
             dependencies=[Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN))],
             summary="Envoyer un message aux RH (crée une notification par destinataire)")
def message_rh(req: MessageRhRequest, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)) -> MessageRhResult:
    """Un manager communique avec les RH : crée une notification pour chaque RH/ADMIN."""
    n = notification_service.communiquer_aux_rh(
        db, from_name=user.name, sujet=req.sujet, message=req.message)
    return MessageRhResult(destinataires=n)


@router.post("/message-profil", response_model=MessageProfilResult,
             dependencies=[Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN))],
             summary="Notifier un collaborateur (RH/manager → profil)")
def message_profil(req: MessageProfilRequest, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> MessageProfilResult:
    """Envoie une notification ciblée au collaborateur d'un profil. Ownership :
    RH/ADMIN global ; MANAGER borné à son équipe (403 hors périmètre)."""
    ownership.require_profil_view(db, user, req.profil_id)  # 404 si absent, 403 hors périmètre
    delivered = notification_service.message_a_profil(
        db, profil_id=req.profil_id, from_name=user.name,
        sujet=req.sujet, message=req.message, to_route=req.to_route)
    return MessageProfilResult(delivered=delivered)


@router.get("", response_model=list[NotificationOut],
            summary="Mes notifications (utilisateur authentifié)")
def mes_notifications(
    only_unread: bool = Query(False, description="Ne renvoyer que les non-lues."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationOut]:
    return notification_service.list_notifications(
        db, user.id, only_unread=only_unread, limit=limit, offset=offset)


@router.patch("/{notification_id}/lu", response_model=NotificationOut,
              summary="Marquer une notification comme lue")
def marquer_lue(notification_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> NotificationOut:
    out = notification_service.mark_read(db, notification_id, user.id)
    if out is None:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return out


@router.post("/lues", summary="Marquer toutes mes notifications comme lues")
def marquer_toutes_lues(user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> dict:
    n = notification_service.mark_all_read(db, user.id)
    return {"marquees_lues": n}
