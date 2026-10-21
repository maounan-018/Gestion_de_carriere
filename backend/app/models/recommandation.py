#!/usr/bin/env python3
"""
models/recommandation.py — Recommandation de carrière PERSISTÉE.

RÔLE
    Stocke le résultat de la reco (pipeline IA) comme SOURCE DURABLE, au lieu du
    seul cache mémoire (perdu au redémarrage). Une ligne par état de profil
    (identifié par `signature` = hash profil + poste visé + compétences détenues) :
    recalculer un profil INCHANGÉ met à jour la même ligne (jamais de perte) ;
    changer l'objectif/les compétences change la signature => nouvelle ligne
    (léger historique par objectif). Le cache mémoire redevient une simple
    optimisation devant cette source persistée.

EMPLACEMENT MVC
    Couche "models" : table + colonnes.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Recommandation(Base):
    __tablename__ = "recommandations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profil_id: Mapped[int] = mapped_column(ForeignKey("profils.id"), index=True)
    signature: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )  # sha256 hex des entrées
    poste_vise: Mapped[str | None] = mapped_column(String(300), default=None)
    score: Mapped[int | None] = mapped_column(Integer, default=None)  # adéquation actuelle (0-100)
    contenu_json: Mapped[str] = mapped_column(Text)  # résultat complet (JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
