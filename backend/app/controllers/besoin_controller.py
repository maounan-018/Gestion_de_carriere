#!/usr/bin/env python3
"""
controllers/besoin_controller.py — Besoins de recrutement (manager → HRBP → offre).

Le manager exprime/transmet un besoin ; la HRBP le liste, valide/refuse, puis
publie l'offre en continuité (visibilité partagée via Offre.manager_id).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.models.user import User, Role
from app.schemas.besoin import BesoinCreate, BesoinOut, BesoinRefus, BesoinPublier, BesoinContact
from app.schemas.offre import OffreOut
from app.services import besoin_service

router = APIRouter(prefix="/api/besoins", tags=["Besoins de recrutement"])


@router.post("", response_model=BesoinOut, status_code=201,
             summary="Exprimer un besoin de recrutement (manager) → transmis à la HRBP")
def creer(data: BesoinCreate,
          user: User = Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN)),
          db: Session = Depends(get_db)) -> BesoinOut:
    return besoin_service.creer_besoin(db, user.id, data)


@router.get("/mes", response_model=list[BesoinOut],
            summary="Mes besoins de recrutement (manager) — suivi de statut")
def mes_besoins(user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> list[BesoinOut]:
    return besoin_service.mes_besoins(db, user.id)


@router.get("", response_model=list[BesoinOut],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Lister les besoins de recrutement (HRBP) — option filtre statut")
def lister(statut: str | None = Query(None), db: Session = Depends(get_db)) -> list[BesoinOut]:
    return besoin_service.lister_besoins(db, statut)


@router.get("/{besoin_id}", response_model=BesoinOut,
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Détail d'un besoin de recrutement (HRBP)")
def detail(besoin_id: int, db: Session = Depends(get_db)) -> BesoinOut:
    out = besoin_service.get_besoin(db, besoin_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Besoin introuvable")
    return out


@router.post("/{besoin_id}/contacter", status_code=204,
             summary="Contacter le manager émetteur du besoin (HRBP)")
def contacter(besoin_id: int, data: BesoinContact,
              user: User = Depends(require_roles(Role.RH, Role.ADMIN)),
              db: Session = Depends(get_db)) -> None:
    if not besoin_service.contacter_manager(db, besoin_id, user.name, data.message):
        raise HTTPException(status_code=404, detail="Besoin introuvable")


@router.post("/{besoin_id}/valider", response_model=BesoinOut,
             summary="Valider un besoin (HRBP)")
def valider(besoin_id: int,
            user: User = Depends(require_roles(Role.RH, Role.ADMIN)),
            db: Session = Depends(get_db)) -> BesoinOut:
    out = besoin_service.valider(db, besoin_id, user.id)
    if out is None:
        raise HTTPException(status_code=404, detail="Besoin introuvable")
    return out


@router.post("/{besoin_id}/refuser", response_model=BesoinOut,
             summary="Refuser un besoin (HRBP)")
def refuser(besoin_id: int, data: BesoinRefus,
            user: User = Depends(require_roles(Role.RH, Role.ADMIN)),
            db: Session = Depends(get_db)) -> BesoinOut:
    out = besoin_service.refuser(db, besoin_id, user.id, data.motif)
    if out is None:
        raise HTTPException(status_code=404, detail="Besoin introuvable")
    return out


@router.post("/{besoin_id}/publier", response_model=OffreOut,
             summary="Publier l'offre en continuité du besoin (HRBP) — visibilité partagée manager")
def publier(besoin_id: int, data: BesoinPublier,
            user: User = Depends(require_roles(Role.RH, Role.ADMIN)),
            db: Session = Depends(get_db)) -> OffreOut:
    offre, besoin = besoin_service.publier(db, besoin_id, user.id, data)
    if offre is None:
        raise HTTPException(status_code=404, detail="Besoin introuvable")
    return offre
