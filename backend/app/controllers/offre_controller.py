#!/usr/bin/env python3
"""
controllers/offre_controller.py — Routes HTTP des Offres (poste / mission / projet / gig).

RÔLE
    Expose le CRUD de l'offre et de ses attendus overridables. Sans logique métier :
    valide l'entrée (schemas), délègue au service, traduit l'absence en 404 et une
    référence invalide (Fiche inexistante) en 400.

SÉCURITÉ (RBAC branché — Bloc C)
    Création/édition réservées à RH/MANAGER/ADMIN. Règle type↔rôle : la RH ne pousse
    que des `offre_poste`, un MANAGER que des `mission`/`projet`/`gig` (l'ADMIN, tout).
    `created_by` est TOUJOURS l'utilisateur de la session (jamais fourni par le
    client). Lecture ouverte à tout utilisateur authentifié. CSRF vérifié sur les
    méthodes mutantes. TODO B2 : périmètre du MANAGER (département/équipe).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue aux services.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.models.user import User, Role
from app.models.offre import Offre
from app.models.candidature import Candidature, CandidatureStatut
from app.schemas.offre import (OffreCreate, OffreUpdate, OffreOut,
                               OffreCompetenceIn, OffreCompetenceUpdate, OffreCompatOut,
                               OffreCandidatOut, RhOffreOut, VacancyOut,
                               MissionEvalContextOut, MissionExpectedComp,
                               MissionParticipantOut, MissionEvaluationIn, MissionEvaluationOut)
from app.services import offre_service, evaluation_service

router = APIRouter(prefix="/api/offres", tags=["Offres"])


def _offre_du_manager(db: Session, offre_id: int, user: User) -> Offre:
    """Charge l'offre et vérifie que l'utilisateur en est le manager créateur
    (ou RH/ADMIN). 404 si absente, 403 hors périmètre."""
    offre = db.get(Offre, offre_id)
    if offre is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if user.role not in (Role.RH, Role.ADMIN) and offre.created_by != user.id:
        raise HTTPException(status_code=403,
                            detail="Réservé au manager de l'offre (ou RH/ADMIN).")
    return offre


@router.get("/{offre_id}/participants", response_model=MissionEvalContextOut,
            summary="Contexte d'évaluation de mission : offre + compétences + participants retenus")
def contexte_evaluation_mission(offre_id: int, user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)) -> MissionEvalContextOut:
    """Écran d'évaluation post-clôture : renvoie l'offre, ses compétences attendues
    et ses PARTICIPANTS RETENUS. Réservé au manager de l'offre (ou RH/ADMIN)."""
    offre = _offre_du_manager(db, offre_id, user)
    out = offre_service.get_offre(db, offre_id)
    comps = [MissionExpectedComp(libelle=c.skill_label_fr or c.libelle,
                                 skill_id=c.skill_id, importance=c.importance)
             for c in (out.competences if out else [])]
    parts = [MissionParticipantOut(**p) for p in offre_service.mission_participants(db, offre_id)]
    return MissionEvalContextOut(
        offre_id=offre.id, titre=offre.titre, type=offre.type, statut=offre.statut,
        competences=comps, participants=parts)


@router.post("/{offre_id}/participants/{profil_id}/evaluation",
             response_model=MissionEvaluationOut,
             summary="Évaluer (1-10) les compétences utilisées par un participant retenu")
def evaluer_participant_mission(offre_id: int, profil_id: int, data: MissionEvaluationIn,
                                user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)) -> MissionEvaluationOut:
    """Le manager note les compétences UTILISÉES par un participant dans la mission.
    Une compétence notée mais absente du profil y est AJOUTÉE (source
    evaluation_mission) avec l'attribution (évaluateur + mission). Le profil doit
    être un participant RETENU de cette offre."""
    _offre_du_manager(db, offre_id, user)
    cand = db.scalar(select(Candidature).where(
        Candidature.offre_id == offre_id, Candidature.profil_id == profil_id,
        Candidature.statut == CandidatureStatut.RETENUE))
    if cand is None:
        raise HTTPException(status_code=400,
                            detail="Ce profil n'est pas un participant retenu de cette offre.")
    res = evaluation_service.evaluer_mission(
        db, profil_id=profil_id, offre_id=offre_id, evaluateur_id=user.id,
        items=[c.model_dump() for c in data.competences])
    return MissionEvaluationOut(**res)

# Types d'offre autorisés par rôle (l'ADMIN n'est pas restreint).
_TYPES_PAR_ROLE = {
    Role.RH: {"offre_poste"},
    Role.MANAGER: {"mission", "projet", "gig"},
}


@router.post("", response_model=OffreOut, status_code=201,
             summary="Créer une offre (dérive d'une Fiche : attendus copiés puis overridables)")
def creer_offre(data: OffreCreate,
                user: User = Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN)),
                db: Session = Depends(get_db)) -> OffreOut:
    # Règle type↔rôle : chaque rôle ne publie que ses types d'offre (ADMIN : tout).
    autorises = _TYPES_PAR_ROLE.get(user.role)
    if autorises is not None and data.type not in autorises:
        raise HTTPException(
            status_code=403,
            detail=f"Le rôle {user.role} ne peut pas publier une offre de type « {data.type} ».")
    # Identité côté serveur : le pousseur est TOUJOURS la session (anti-usurpation).
    data.created_by = user.id
    try:
        return offre_service.create_offre(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[OffreOut],
            dependencies=[Depends(get_current_user)],
            summary="Lister les offres (filtres statut / type / département / fiche)")
def lister_offres(
    statut: str | None = Query(None, description="brouillon | ouverte | pourvue | fermee | annulee"),
    type: str | None = Query(None, description="offre_poste | mission | projet | gig"),
    departement_key: str | None = Query(None),
    fiche_id: int | None = Query(None, description="Offres dérivées d'une Fiche donnée."),
    synthetique: bool | None = Query(None, description="Filtrer données de démo (true) ou réelles (false)."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[OffreOut]:
    return offre_service.list_offres(
        db, statut=statut, type=type, departement_key=departement_key,
        fiche_id=fiche_id, synthetique=synthetique, limit=limit, offset=offset)


@router.get("/compatibles", response_model=list[OffreCompatOut],
            summary="Offres + % de compatibilité pour le profil du compte connecté")
def offres_compatibles(user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> list[OffreCompatOut]:
    return offre_service.list_compatibles_for_user(db, user.id)


@router.get("/rh-liste", response_model=list[RhOffreOut],
            dependencies=[Depends(require_roles(Role.RH, Role.ADMIN))],
            summary="Offres côté RH avec statistiques de candidatures (liste + revue)")
def offres_rh(db: Session = Depends(get_db)) -> list[RhOffreOut]:
    return offre_service.rh_offres(db)


@router.get("/vacances", response_model=list[VacancyOut],
            summary="Postes de l'équipe du manager + profils internes recommandés (matching inverse)")
def offres_vacances(user: User = Depends(require_roles(Role.MANAGER, Role.RH, Role.ADMIN)),
                    db: Session = Depends(get_db)) -> list[VacancyOut]:
    return offre_service.vacancies_for_manager(db, user.id)


@router.get("/{offre_id}/candidats", response_model=list[OffreCandidatOut],
            dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
            summary="Candidats d'une offre (score + couvertes/écarts) — écran revue RH")
def candidats_offre(offre_id: int, db: Session = Depends(get_db)) -> list[OffreCandidatOut]:
    return offre_service.list_candidats_offre(db, offre_id)


@router.get("/{offre_id}", response_model=OffreOut,
            dependencies=[Depends(get_current_user)],
            summary="Consulter une offre et ses attendus")
def consulter_offre(offre_id: int, db: Session = Depends(get_db)) -> OffreOut:
    out = offre_service.get_offre(db, offre_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return out


@router.patch("/{offre_id}", response_model=OffreOut,
              dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
              summary="Mettre à jour une offre (dont transition de statut)")
def modifier_offre(offre_id: int, data: OffreUpdate, db: Session = Depends(get_db)) -> OffreOut:
    out = offre_service.update_offre(db, offre_id, data)
    if out is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return out


@router.post("/{offre_id}/competences", response_model=OffreOut,
             dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
             summary="Ajouter des attendus à une offre")
def ajouter_attendus(offre_id: int, comps: list[OffreCompetenceIn],
                     db: Session = Depends(get_db)) -> OffreOut:
    out = offre_service.add_competences(db, offre_id, comps)
    if out is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return out


@router.patch("/{offre_id}/competences/{comp_id}", response_model=OffreOut,
              dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
              summary="Override un attendu (importance / niveau / libellé) au niveau de l'offre")
def modifier_attendu(offre_id: int, comp_id: int, data: OffreCompetenceUpdate,
                     db: Session = Depends(get_db)) -> OffreOut:
    out = offre_service.update_competence(db, offre_id, comp_id, data)
    if out is None:
        raise HTTPException(status_code=404, detail="Offre ou attendu introuvable")
    return out


@router.delete("/{offre_id}/competences/{comp_id}", response_model=OffreOut,
               dependencies=[Depends(require_roles(Role.RH, Role.MANAGER, Role.ADMIN))],
               summary="Retirer un attendu de l'offre")
def supprimer_attendu(offre_id: int, comp_id: int,
                      db: Session = Depends(get_db)) -> OffreOut:
    out = offre_service.delete_competence(db, offre_id, comp_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Offre ou attendu introuvable")
    return out
