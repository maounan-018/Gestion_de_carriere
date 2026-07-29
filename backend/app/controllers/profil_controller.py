#!/usr/bin/env python3
"""
controllers/profil_controller.py — Routes HTTP du Profil collaborateur.

RÔLE
    Expose le CRUD du profil en API REST. Sans logique métier : valide l'entrée
    (schemas), délègue au service, traduit l'absence en 404.

SÉCURITÉ (RBAC + ownership B2)
    Écriture (créer / éditer / ajouter des compétences) réservée à RH/ADMIN.
    Ownership ligne-à-ligne (cf. `auth/ownership.py`) : la LISTE est bornée au
    périmètre (MANAGER = son équipe ; RH/ADMIN = global) et la LECTURE unitaire d'un
    profil est réservée au propriétaire (COLLAB), à son manager, ou à RH/ADMIN.
    L'annuaire reste un répertoire LIMITÉ ouvert à tout authentifié. Le CSRF est
    vérifié par get_current_user sur les méthodes mutantes.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.auth import ownership
from app.models.user import Role, User
from app.schemas.profil import (ProfilCreate, ProfilUpdate, ProfilSelfUpdate, ProfilOut,
                                 ProfilCompetenceIn, AnnuaireEntry)
from app.schemas.carriere import ProfilCarriereOut
from app.services import profil_service

router = APIRouter(prefix="/api/profils", tags=["Profils"])


@router.post("", response_model=ProfilOut, status_code=201,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
             summary="Créer un profil collaborateur (+ compétences initiales)")
def creer_profil(data: ProfilCreate, db: Session = Depends(get_db)) -> ProfilOut:
    return profil_service.create_profil(db, data)


@router.get("", response_model=list[ProfilOut],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN, Role.MANAGER))],
            summary="Lister les profils (filtres département / persona / équipe d'un manager)")
def lister_profils(
    departement_key: str | None = Query(None),
    synthetique: bool | None = Query(None, description="Filtrer personas de démo (true) ou réels (false)."),
    manager_id: int | None = Query(None, description="Équipe d'un manager (profils dont le compte a ce manager)."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProfilOut]:
    # Ownership B2 : un MANAGER est borné à SON équipe (on force son périmètre,
    # quel que soit le manager_id demandé). RH/ADMIN : périmètre global (libre).
    if user.role == Role.MANAGER:
        manager_id = user.id
    return profil_service.list_profils(db, departement_key=departement_key,
                                       synthetique=synthetique, manager_id=manager_id,
                                       limit=limit, offset=offset)


@router.get("/me/carriere", response_model=ProfilCarriereOut,
            dependencies=[Depends(get_current_user)],
            summary="Ma vue carrière (profil lié au compte connecté)")
def ma_carriere(user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> ProfilCarriereOut:
    out = profil_service.get_carriere_for_user(db, user.id)
    if out is None:
        raise HTTPException(status_code=404, detail="Aucun profil de carrière lié à ce compte.")
    return out


@router.patch("/me", response_model=ProfilOut,
              summary="Éditer MON profil (auto-service : poste visé / aspirations / poste actuel)")
def modifier_mon_profil(data: ProfilSelfUpdate,
                        user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> ProfilOut:
    out = profil_service.update_self(db, user.id, data)
    if out is None:
        raise HTTPException(status_code=404, detail="Aucun profil lié à ce compte.")
    return out


@router.get("/annuaire", response_model=list[AnnuaireEntry],
            dependencies=[Depends(get_current_user)],
            summary="Annuaire (répertoire limité, accessible à tout utilisateur authentifié)")
def annuaire(departement_key: str | None = Query(None),
             limit: int = Query(200, ge=1, le=500),
             offset: int = Query(0, ge=0),
             db: Session = Depends(get_db)) -> list[AnnuaireEntry]:
    return profil_service.list_annuaire(db, departement_key=departement_key,
                                        limit=limit, offset=offset)


@router.get("/{profil_id}/carriere", response_model=ProfilCarriereOut,
            summary="Vue carrière enrichie (aspirations, compétences, stations, avis des pairs)")
def carriere_profil(profil_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)) -> ProfilCarriereOut:
    ownership.require_profil_view(db, user, profil_id)   # 404 si absent, 403 hors périmètre
    out = profil_service.get_carriere(db, profil_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return out


@router.get("/{profil_id}", response_model=ProfilOut,
            summary="Consulter un profil et ses compétences")
def consulter_profil(profil_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)) -> ProfilOut:
    ownership.require_profil_view(db, user, profil_id)   # 404 si absent, 403 hors périmètre
    out = profil_service.get_profil(db, profil_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return out


@router.patch("/{profil_id}", response_model=ProfilOut,
              dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
              summary="Mettre à jour un profil (dont aspirations / poste visé)")
def modifier_profil(profil_id: int, data: ProfilUpdate, db: Session = Depends(get_db)) -> ProfilOut:
    out = profil_service.update_profil(db, profil_id, data)
    if out is None:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return out


@router.post("/{profil_id}/competences", response_model=ProfilOut,
             dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
             summary="Ajouter des compétences détenues à un profil")
def ajouter_competences(profil_id: int, comps: list[ProfilCompetenceIn],
                        db: Session = Depends(get_db)) -> ProfilOut:
    out = profil_service.add_competences(db, profil_id, comps)
    if out is None:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return out
