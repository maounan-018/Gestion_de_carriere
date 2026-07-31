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
from app.auth.dependencies import get_current_user, require_roles
from app.core.rate_limit import ia_rate_limit
from app.models.user import Role
from app.schemas.formation import FormationOut, FormationGenerationRequest, FormationGeneree
from app.services import formation_service, formation_generation_service

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


@router.post("/generer", response_model=FormationGeneree,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN)), Depends(ia_rate_limit)],
             summary="Générer une formation synthétique pour une compétence (RH/ADMIN)")
def generer_formation(req: FormationGenerationRequest,
                      db: Session = Depends(get_db)) -> FormationGeneree:
    """⚠️ Utilise Ollama (génération FR). Contenu SYNTHÉTIQUE (jamais un cours réel).
    Si `persister`, ajoute la formation au catalogue et renvoie son `id`."""
    gen = formation_generation_service.generer(db, req.competence)
    if req.persister:
        gen["id"] = formation_service.create_formation(db, gen).id
    return FormationGeneree(**gen)
