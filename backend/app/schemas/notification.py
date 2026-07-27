#!/usr/bin/env python3
"""
schemas/notification.py — Contrats de sortie d'une Notification.

RÔLE
    Forme minimale exposée au front (cloche de notifications). Le cloisonnement
    est assuré côté service : on ne renvoie que les notifications de l'utilisateur
    authentifié.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    titre: str
    texte: str | None
    to_route: str | None
    lu: bool
    created_at: datetime
