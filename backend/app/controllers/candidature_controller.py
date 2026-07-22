#!/usr/bin/env python3
"""
controllers/candidature_controller.py — Routes HTTP des Candidatures (profil ↔ offre).

RÔLE
    Expose le dépôt et le suivi des candidatures. Le score est calculé côté
    serveur au dépôt (jamais fourni par le client). Sans logique métier : valide
    l'entrée, délègue au service, traduit l'absence en 404 et un conflit (offre/
    profil inexistant, double candidature) en 400.

SÉCURITÉ (à durcir — Bloc C)
    TODO RBAC : un COLLAB candidate pour lui-même (profil_id = le sien) ; RH/MANAGER
    consultent les candidats d'une offre de leur périmètre et portent la décision
    (`PATCH /decision`). À restreindre via Depends(get_current_user) + guard de rôle
    à la passe sécurité. Ouvert ici, comme profil_controller, pour l'itération data.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.candidature import (CandidatureCreate, CandidatureDecision,
                                     CandidatureOut)
from app.services import candidature_service

router = APIRouter(prefix="/api/candidatures", tags=["Candidatures"])


@router.post("", response_model=CandidatureOut, status_code=201,
             summary="Déposer une candidature (score + écarts calculés au dépôt)")
def deposer_candidature(data: CandidatureCreate, db: Session = Depends(get_db)) -> CandidatureOut:
    try:
        return candidature_service.create_candidature(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[CandidatureOut],
            summary="Lister les candidatures (candidats d'une offre, ou candidatures d'un profil)")
def lister_candidatures(
    offre_id: int | None = Query(None, description="Candidats d'une offre (tri par score décroissant)."),
    profil_id: int | None = Query(None, description="Candidatures déposées par un profil."),
    statut: str | None = Query(None, description="deposee | en_evaluation | retenue | rejetee | retiree"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[CandidatureOut]:
    return candidature_service.list_candidatures(
        db, offre_id=offre_id, profil_id=profil_id, statut=statut,
        limit=limit, offset=offset)


@router.get("/{candidature_id}", response_model=CandidatureOut,
            summary="Consulter une candidature et son snapshot d'évaluation")
def consulter_candidature(candidature_id: int, db: Session = Depends(get_db)) -> CandidatureOut:
    out = candidature_service.get_candidature(db, candidature_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out


@router.patch("/{candidature_id}/decision", response_model=CandidatureOut,
              summary="Décision humaine (retenue possible même si score < 100 %)")
def decider_candidature(candidature_id: int, data: CandidatureDecision,
                        db: Session = Depends(get_db)) -> CandidatureOut:
    out = candidature_service.decide_candidature(db, candidature_id, data.statut, data.decided_by)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out


@router.post("/{candidature_id}/reevaluation", response_model=CandidatureOut,
             summary="Recalculer le score (attendus de l'offre modifiés depuis le dépôt)")
def reevaluer_candidature(candidature_id: int, db: Session = Depends(get_db)) -> CandidatureOut:
    out = candidature_service.reevaluer_candidature(db, candidature_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    return out
