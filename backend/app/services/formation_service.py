#!/usr/bin/env python3
"""
services/formation_service.py — Catalogue de formations (lecture + recherche).

RÔLE
    Liste/filtre le catalogue de formations synthétiques (par domaine ou par
    compétence visée). Sert l'écran Formations et, plus tard, la recommandation
    (proposer une formation en réponse à un écart de compétence).

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.formation import Formation
from app.schemas.formation import FormationOut


def _lower(col):
    """LOWER(col) tolérant au NULL (COALESCE → '') pour la recherche texte."""
    return func.lower(func.coalesce(col, ""))


def list_formations(db: Session, *, domaine: str | None = None, q: str | None = None,
                    limit: int = 100, offset: int = 0) -> list[FormationOut]:
    """Catalogue filtrable par domaine et par texte (titre/compétence visée/tags)."""
    stmt = select(Formation).order_by(Formation.domaine, Formation.titre)
    if domaine is not None:
        stmt = stmt.where(Formation.domaine == domaine)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            _lower(Formation.titre).like(like)
            | _lower(Formation.skill_cible).like(like)
            | _lower(Formation.tags).like(like)
        )
    stmt = stmt.limit(min(max(limit, 1), 300)).offset(max(offset, 0))
    return [FormationOut.model_validate(f) for f in db.scalars(stmt).all()]
