#!/usr/bin/env python3
"""
services/notification_service.py — Logique métier des notifications.

RÔLE
    Liste les notifications d'un utilisateur (les siennes uniquement) et gère leur
    lecture. La création est surtout utilisée par le seed et, plus tard, par les
    évènements métier (nouvelle offre compatible, souhait consulté…).

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import NotificationOut


def list_notifications(
    db: Session, user_id: int, *, only_unread: bool = False, limit: int = 50, offset: int = 0
) -> list[NotificationOut]:
    """Notifications de l'utilisateur, plus récentes d'abord."""
    stmt = select(Notification).where(Notification.user_id == user_id)
    if only_unread:
        stmt = stmt.where(Notification.lu.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
    stmt = stmt.limit(min(max(limit, 1), 200)).offset(max(offset, 0))
    return [NotificationOut.model_validate(n) for n in db.scalars(stmt).all()]


def count_unread(db: Session, user_id: int) -> int:
    return len(
        db.scalars(
            select(Notification.id).where(
                Notification.user_id == user_id, Notification.lu.is_(False)
            )
        ).all()
    )


def mark_read(db: Session, notification_id: int, user_id: int) -> NotificationOut | None:
    """Marque une notification comme lue. None si absente OU pas au bon
    destinataire (on ne révèle pas l'existence d'une notification d'autrui)."""
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        return None
    n.lu = True
    db.commit()
    db.refresh(n)
    return NotificationOut.model_validate(n)


def mark_all_read(db: Session, user_id: int) -> int:
    """Marque toutes les notifications de l'utilisateur comme lues. Renvoie le nb touché."""
    res = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.lu.is_(False))
        .values(lu=True)
    )
    db.commit()
    return res.rowcount or 0


def create_notification(
    db: Session,
    *,
    user_id: int,
    titre: str,
    type: str = "info",
    texte: str | None = None,
    to_route: str | None = None,
    commit: bool = True,
) -> Notification:
    """Crée une notification (usage seed / évènements métier)."""
    n = Notification(user_id=user_id, type=type, titre=titre, texte=texte, to_route=to_route)
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)
    return n


def communiquer_aux_rh(
    db: Session, *, from_name: str, sujet: str, message: str, to_route: str = "rh.notifications"
) -> int:
    """Crée une notification pour CHAQUE utilisateur RH/ADMIN (message d'un manager).
    `to_route` = écran ciblé au clic (défaut : les notifications). Renvoie le nombre
    de destinataires. Une seule transaction."""
    from app.models.user import Role, User

    rh = db.scalars(select(User).where(User.role.in_([Role.RH, Role.ADMIN]))).all()
    titre = (sujet.strip() or f"Message de {from_name}")[:200]
    texte = f"De {from_name} (manager) : {message.strip()}"[:1000]
    for u in rh:
        create_notification(
            db, user_id=u.id, titre=titre, type="info", texte=texte, to_route=to_route, commit=False
        )
    db.commit()
    return len(rh)


def message_a_profil(
    db: Session,
    *,
    profil_id: int,
    from_name: str,
    sujet: str,
    message: str,
    to_route: str | None = None,
) -> bool:
    """Notifie le collaborateur d'un profil (RH/manager → collaborateur). Renvoie
    True si une notification a été créée, False si le profil n'a pas de compte
    utilisateur actif (persona synthétique)."""
    from app.models.profil import Profil

    profil = db.get(Profil, profil_id)
    if profil is None or profil.user_id is None:
        return False
    titre = (f"{sujet.strip()} — {from_name}" if sujet.strip() else f"Message de {from_name}")[:200]
    create_notification(
        db,
        user_id=profil.user_id,
        titre=titre,
        type="info",
        texte=message.strip()[:1000],
        to_route=to_route,
    )
    return True
