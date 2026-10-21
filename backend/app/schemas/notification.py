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

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    titre: str
    texte: str | None
    to_route: str | None
    lu: bool
    created_at: datetime


class MessageRhRequest(BaseModel):
    """Message d'un manager à destination des RH (crée une notification par RH)."""

    sujet: str = Field("", max_length=200, description="Sujet (optionnel).")
    message: str = Field(..., min_length=1, max_length=1000, description="Corps du message.")


class MessageRhResult(BaseModel):
    destinataires: int  # nombre de RH/ADMIN notifiés


class MessageProfilRequest(BaseModel):
    """Message ciblé vers un collaborateur (RH/manager → profil). Crée une
    notification pour le compte du collaborateur, s'il en possède un."""

    profil_id: int = Field(..., description="Profil du collaborateur destinataire.")
    sujet: str = Field("", max_length=200, description="Sujet (optionnel).")
    message: str = Field(..., min_length=1, max_length=1000, description="Corps du message.")
    to_route: str | None = Field(None, max_length=64, description="Route de destination (front).")


class MessageProfilResult(BaseModel):
    delivered: bool  # False si le profil n'a pas de compte utilisateur actif
