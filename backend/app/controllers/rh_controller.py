#!/usr/bin/env python3
"""
controllers/rh_controller.py — Vues analytiques RH (veille & alertes).

RÔLE
    Expose la veille des entretiens et les alertes RH dérivées de signaux réels,
    calculées par `dashboard_service`.

SÉCURITÉ (RBAC)
    Réservé RH/ADMIN (vue globale de la banque).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.core.rate_limit import ia_rate_limit
from app.models.user import Role, User
from app.schemas.dashboard import VeilleItem, AlerteItem, AnalyseRhOut
from app.schemas.succession import (
    SuccessionRequest, SuccessionResponse, SuccessionJobLaunched, SuccessionJobStatus,
)
from app.services import dashboard_service, succession_service, analyse_service

router = APIRouter(prefix="/api/rh", tags=["RH"],
                   dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))])


@router.get("/veille", response_model=list[VeilleItem],
            summary="Veille des entretiens (réalisés / planifiés / en retard)")
def veille(db: Session = Depends(get_db)) -> list[VeilleItem]:
    return dashboard_service.veille(db)


@router.get("/alertes", response_model=list[AlerteItem],
            summary="Alertes RH dérivées (potentiels, entretiens en retard, mobilité)")
def alertes(db: Session = Depends(get_db)) -> list[AlerteItem]:
    return dashboard_service.alertes(db)


@router.post("/analyse", response_model=AnalyseRhOut,
             dependencies=[Depends(ia_rate_limit)],
             summary="Analyse stratégique RH par l'IA (synthèse des indicateurs consolidés)")
def analyse(db: Session = Depends(get_db)) -> AnalyseRhOut:
    """⚠️ Utilise le LLM local (mistral-nemo) : quelques secondes. Fait « lire » par
    l'IA les indicateurs consolidés de la plateforme (tensions de compétences, hauts
    potentiels, rétention, qualité des données) et produit une synthèse stratégique
    actionnable pour la RH."""
    return AnalyseRhOut(**analyse_service.analyser(db))


@router.get("/analyse/latest", response_model=AnalyseRhOut | None,
            summary="Dernière analyse stratégique HRBP PERSISTÉE (sans relancer le LLM ; null si aucune)")
def analyse_latest(db: Session = Depends(get_db)) -> AnalyseRhOut | None:
    """Présentation immédiate du tableau de bord HRBP : renvoie la dernière
    synthèse persistée (rapide), sans appel LLM. `null` si aucune analyse n'a
    encore été produite — le front invitera alors à en générer une."""
    data = analyse_service.charger_derniere(db)
    return AnalyseRhOut(**data) if data else None


@router.post("/succession", response_model=SuccessionResponse,
             summary="Plan de succession CALCULÉ d'un pôle (déterministe, instantané)")
def succession(req: SuccessionRequest, db: Session = Depends(get_db)) -> SuccessionResponse:
    """Pour chaque poste d'ENCADREMENT du pôle : successeurs internes classés par
    adéquation de compétences (recouvrement pondéré par niveau au poste du titulaire),
    niveau de préparation, écarts à combler et postes clés À RISQUE. Aucun LLM →
    réponse instantanée et reproductible."""
    return SuccessionResponse(**succession_service.plan_succession(db, req.departement_key))


@router.post("/succession/async", response_model=SuccessionJobLaunched, status_code=202,
             summary="Lancer le plan de succession en tâche de fond (renvoie un job_id)")
def lancer_succession(req: SuccessionRequest,
                      user: User = Depends(get_current_user)) -> SuccessionJobLaunched:
    """Variante asynchrone (rétrocompat) : calcule le plan en tâche de fond et renvoie
    aussitôt un `job_id`. Le front interroge ensuite `/succession/jobs/{job_id}`. Le
    calcul étant désormais déterministe/instantané, `/succession` (synchrone) suffit."""
    return SuccessionJobLaunched(
        job_id=succession_service.launch_succession_job(user.id, req.departement_key))


@router.get("/succession/jobs/{job_id}", response_model=SuccessionJobStatus,
            summary="État de mon job de succession (pending / done + résultat / error)")
def statut_succession(job_id: str,
                      user: User = Depends(get_current_user)) -> SuccessionJobStatus:
    job = succession_service.get_succession_job(job_id, user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job de succession inconnu ou expiré.")
    return SuccessionJobStatus(**job)
