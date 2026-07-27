#!/usr/bin/env python3
"""
controllers/formation_controller.py — Routes du catalogue de formations.

RÔLE
    Expose le catalogue de formations synthétiques (lecture/recherche), pour
    l'écran Formations et la recommandation. Ouvert à tout utilisateur authentifié.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.schemas.formation import FormationOut
from app.services import formation_service

router = APIRouter(prefix="/api/formations", tags=["Formations"])


@router.get("", response_model=list[FormationOut],
            dependencies=[Depends(get_current_user)],
            summary="Catalogue de formations (filtres domaine / texte)")
def lister_formations(
    domaine: str | None = Query(None, description="Filtrer par domaine/thème."),
    q: str | None = Query(None, description="Recherche texte (titre / compétence visée / tags)."),
    limit: int = Query(100, ge=1, le=300),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[FormationOut]:
    return formation_service.list_formations(db, domaine=domaine, q=q, limit=limit, offset=offset)
