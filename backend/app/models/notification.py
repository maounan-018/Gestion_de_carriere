#!/usr/bin/env python3
"""
models/notification.py — Notification destinée à un utilisateur.

RÔLE
    Message court poussé à un utilisateur (collaborateur, manager, RH) : nouvelle
    offre compatible, souhait consulté, entretien à préparer, décision… Alimente
    les cloches de notification des trois espaces. Chaque notification appartient
    à UN destinataire (`user_id`) — le cloisonnement se fait par cet utilisateur.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NotificationType:
    INFO = "info"  # information générale
    OFFRE = "offre"  # offre/mobilité compatible
    ENTRETIEN = "entretien"  # entretien à préparer / planifié
    SOUHAIT = "souhait"  # souhait d'évolution (consulté, poussé…)
    ACTION = "action"  # action attendue de l'utilisateur


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # destinataire
    type: Mapped[str] = mapped_column(String(16), default=NotificationType.INFO)
    titre: Mapped[str] = mapped_column(String(200))
    texte: Mapped[str | None] = mapped_column(Text, default=None)
    to_route: Mapped[str | None] = mapped_column(
        String(64), default=None
    )  # route front de destination
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )
