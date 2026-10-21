#!/usr/bin/env python3
"""
models/besoin.py — Besoin de recrutement (manager → HRBP).

RÔLE
    Un manager n'ouvre plus directement une offre : il EXPRIME un BESOIN de
    recrutement sur un poste (fiche de référence + description), qu'il transmet
    formellement à la HRBP par un canal officiel. La HRBP le VALIDE puis publie
    l'offre EN CONTINUITÉ (l'offre garde la « marque » du manager d'origine via
    `Offre.manager_id`), ce qui donne au manager la MÊME visibilité qu'elle sur
    les candidatures / candidats / CV de l'offre issue de son besoin.

    Cycle : transmis → validé → publié (ou refusé). `offre_id` relie le besoin à
    l'offre finalement publiée.

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BesoinStatut:
    TRANSMIS = "transmis"  # exprimé par le manager, en attente HRBP
    VALIDE = "valide"  # validé par la HRBP (offre à rédiger)
    PUBLIE = "publie"  # offre publiée en continuité
    REFUSE = "refuse"  # non retenu par la HRBP


class BesoinRecrutement(Base):
    __tablename__ = "besoins_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # demandeur
    fiche_id: Mapped[int | None] = mapped_column(ForeignKey("fiches.id"), default=None, index=True)
    poste: Mapped[str] = mapped_column(String(200))  # intitulé visé
    description: Mapped[str | None] = mapped_column(Text, default=None)
    statut: Mapped[str] = mapped_column(String(12), default=BesoinStatut.TRANSMIS, index=True)
    hrbp_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )  # qui traite
    offre_id: Mapped[int | None] = mapped_column(ForeignKey("offres.id"), default=None, index=True)
    motif_refus: Mapped[str | None] = mapped_column(String(400), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
