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
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


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
