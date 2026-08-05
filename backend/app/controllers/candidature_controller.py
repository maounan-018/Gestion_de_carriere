#!/usr/bin/env python3
"""
controllers/candidature_controller.py — Routes HTTP des Candidatures (profil ↔ offre).

RÔLE
    Expose le dépôt et le suivi des candidatures. Le score est calculé côté
    serveur au dépôt (jamais fourni par le client). Sans logique métier : valide
    l'entrée, délègue au service, traduit l'absence en 404 et un conflit (offre/
    profil inexistant, double candidature) en 400.

SÉCURITÉ (RBAC + ownership B2)
    Dépôt réservé à COLLAB/RH/ADMIN ; la décision humaine (`PATCH /decision`) et la
    réévaluation à RH/MANAGER/ADMIN. `decided_by` est TOUJOURS l'utilisateur de la
    session (jamais fourni par le client). Ownership ligne-à-ligne (cf.
    `auth/ownership.py`) : un COLLAB ne candidate que pour SON profil et ne voit que
    SES candidatures ; un MANAGER est borné à son équipe / aux candidats d'une offre ;
    RH/ADMIN sont globaux. CSRF vérifié sur les méthodes mutantes.
    (Différé : périmètre par OFFRE sur decision/réévaluation — cf. ownership.py.)

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.auth import ownership
from app.models.user import User, Role
from app.schemas.candidature import (CandidatureCreate, CandidatureDecision,
                                     CandidatureOut, CandidatureMineOut)
from app.services import candidature_service

router = APIRouter(prefix="/api/candidatures", tags=["Candidatures"])


@router.post("", response_model=CandidatureOut, status_code=201,
             summary="Déposer une candidature (score + écarts calculés au dépôt)")
def deposer_candidature(data: CandidatureCreate,
                        user: User = Depends(require_roles(Role.COLLAB, Role.RH, Role.ADMIN)),
                        db: Session = Depends(get_db)) -> CandidatureOut:
    # Ownership B2 : un COLLAB ne peut candidater que pour SON profil (RH/ADMIN libres).
    ownership.require_own_profil_for_candidature(db, user, data.profil_id)
    try:
        return candidature_service.create_candidature(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


_CV_DIR = os.path.join("data", "cv")   # relatif au cwd du backend (data/cv/{id}.pdf)


@router.post("/{candidature_id}/cv",
             summary="Téléverser le CV (PDF) à jour d'une candidature")
async def uploader_cv(candidature_id: int, fichier: UploadFile = File(...),
                      user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Le candidat (propriétaire) ou RH/ADMIN téléverse le CV à jour (PDF) lié à la
    candidature. Stocké côté serveur (`data/cv/{id}.pdf`)."""
    ownership.require_own_candidature(db, user, candidature_id)   # 404 si absent, 403 hors périmètre
    nom = (fichier.filename or "").lower()
    if (fichier.content_type or "") != "application/pdf" and not nom.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le CV doit être un fichier PDF.")
    data = await fichier.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier CV vide.")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CV trop volumineux (max 10 Mo).")

    def _ecrire() -> None:
        os.makedirs(_CV_DIR, exist_ok=True)
        with open(os.path.join(_CV_DIR, f"{candidature_id}.pdf"), "wb") as f:
            f.write(data)

    # Écriture disque bloquante → threadpool (ne bloque pas l'event loop).
    await run_in_threadpool(_ecrire)
    return {"stored": True, "taille": len(data)}


@router.get("", response_model=list[CandidatureOut],
            summary="Lister les candidatures (candidats d'une offre, ou candidatures d'un profil)")
def lister_candidatures(
    offre_id: int | None = Query(None, description="Candidats d'une offre (tri par score décroissant)."),
    profil_id: int | None = Query(None, description="Candidatures déposées par un profil."),
    statut: str | None = Query(None, description="deposee | en_evaluation | retenue | rejetee | retiree"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CandidatureOut]:
    # Ownership B2 : borne la liste au périmètre (COLLAB=ses candidatures ;
    # MANAGER=offre/équipe ; RH/ADMIN=global). Lève 403 hors périmètre.
    ownership.require_candidature_list_scope(db, user, offre_id, profil_id)
    return candidature_service.list_candidatures(
        db, offre_id=offre_id, profil_id=profil_id, statut=statut,
        limit=limit, offset=offset)


@router.get("/mes", response_model=list[CandidatureMineOut],
            summary="Mes candidatures (profil du compte connecté) + titre/type d'offre")
def mes_candidatures(user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)) -> list[CandidatureMineOut]:
    return candidature_service.list_mine_for_user(db, user.id)


@router.get("/{candidature_id}", response_model=CandidatureOut,
            summary="Consulter une candidature et son snapshot d'évaluation")
def consulter_candidature(candidature_id: int, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> CandidatureOut:
    ownership.require_candidature_view(db, user, candidature_id)  # 404 si absent, 403 hors périmètre
    out = candidature_service.get_candidature(db, candidature_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out


@router.patch("/{candidature_id}/decision", response_model=CandidatureOut,
              summary="Décision humaine (retenue possible même si score < 100 %)")
def decider_candidature(candidature_id: int, data: CandidatureDecision,
                        user: User = Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN)),
                        db: Session = Depends(get_db)) -> CandidatureOut:
    # Le décideur est TOUJOURS l'utilisateur de la session (anti-usurpation).
    out = candidature_service.decide_candidature(db, candidature_id, data.statut, user.id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out


@router.patch("/{candidature_id}/retrait", response_model=CandidatureOut,
              summary="Retirer ma candidature (le candidat renonce → statut « retiree »)")
def retirer_candidature(candidature_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> CandidatureOut:
    # Ownership : seul le candidat (propriétaire du profil) ou RH/ADMIN peut retirer.
    ownership.require_own_candidature(db, user, candidature_id)  # 404 si absent, 403 hors périmètre
    out = candidature_service.retirer_candidature(db, candidature_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out


@router.post("/{candidature_id}/reevaluation", response_model=CandidatureOut,
             dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
             summary="Recalculer le score (attendus de l'offre modifiés depuis le dépôt)")
def reevaluer_candidature(candidature_id: int, db: Session = Depends(get_db)) -> CandidatureOut:
    out = candidature_service.reevaluer_candidature(db, candidature_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out
