#!/usr/bin/env python3
"""
controllers/souhait_controller.py — Routes des souhaits d'évolution.

RÔLE
    Le collaborateur gère SES souhaits (via son profil) et les pousse au manager.
    Le manager (et la RH) consultent les souhaits poussés par leur équipe.

SÉCURITÉ (RBAC + ownership)
    - `GET/POST /api/souhaits` : l'utilisateur agit sur SON profil (ownership).
    - `PATCH /api/souhaits/{id}` : le propriétaire édite ; RH/ADMIN (et le MANAGER
      de l'équipe) peuvent faire évoluer le statut.
    - `GET /api/souhaits/recus` : MANAGER (son équipe) ou RH/ADMIN.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.session import get_db
from app.models.user import Role, User
from app.schemas.souhait import SouhaitCreate, SouhaitOut, SouhaitRecuOut, SouhaitUpdate
from app.services import souhait_service

router = APIRouter(prefix="/api/souhaits", tags=["Souhaits"])


def _profil_id_or_404(db: Session, user: User) -> int:
    profil = souhait_service.profil_of_user(db, user.id)
    if profil is None:
        raise HTTPException(status_code=404, detail="Aucun profil de carrière lié à ce compte.")
    return profil.id


@router.get("", response_model=list[SouhaitOut], summary="Mes souhaits d'évolution")
def mes_souhaits(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SouhaitOut]:
    profil = souhait_service.profil_of_user(db, user.id)
    if profil is None:
        return []
    return souhait_service.list_souhaits(db, profil.id)


@router.post(
    "",
    response_model=SouhaitOut,
    status_code=201,
    summary="Créer un souhait (brouillon ou poussé au manager)",
)
def creer_souhait(
    data: SouhaitCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> SouhaitOut:
    return souhait_service.create_souhait(db, _profil_id_or_404(db, user), data)


@router.get(
    "/recus",
    response_model=list[SouhaitRecuOut],
    dependencies=[Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN))],
    summary="Souhaits poussés par mon équipe (manager)",
)
def souhaits_recus(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SouhaitRecuOut]:
    return souhait_service.list_recus_for_manager(db, user.id)


@router.patch(
    "/{souhait_id}",
    response_model=SouhaitOut,
    summary="Mettre à jour un souhait (propriétaire, ou RH/manager pour le statut)",
)
def modifier_souhait(
    souhait_id: int,
    data: SouhaitUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SouhaitOut:
    s = souhait_service.get_souhait(db, souhait_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Souhait introuvable")
    profil = souhait_service.profil_of_user(db, user.id)
    est_proprietaire = profil is not None and s.profil_id == profil.id
    if not (est_proprietaire or user.role in (Role.RH, Role.ADMIN, Role.MANAGER)):
        raise HTTPException(status_code=403, detail="Droits insuffisants sur ce souhait.")
    return souhait_service.update_souhait(db, souhait_id, data)
