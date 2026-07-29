#!/usr/bin/env python3
"""
auth/ownership.py — Autorisation ligne-à-ligne (row-level ownership).

RÔLE
    Généralise le cloisonnement par PÉRIMÈTRE au-delà du RBAC (rôle) : QUI peut
    voir / agir sur QUELLE ligne. Règle BMCI :
      - COLLAB  : uniquement SON profil (et ses propres candidatures) ;
      - MANAGER : lui + SON ÉQUIPE (collaborateurs dont le compte a manager_id=lui) ;
      - RH / ADMIN : périmètre global.
    Prédicats `can_*` (booléens, pour composer) ; gardes `require_*` (lèvent 404
    « introuvable » ou 403 « hors périmètre » et renvoient l'objet ORM chargé).

    ÉQUIPE alignée sur `profil_service.list_profils(manager_id=…)` : un profil est
    dans l'équipe du manager si son compte lié (`Profil.user_id`) a
    `User.manager_id = <manager>`. Les personas synthétiques (user_id NULL) ne sont
    donc visibles que par RH/ADMIN.

    HORS PÉRIMÈTRE (différé) : le périmètre par OFFRE (un manager ne décide que des
    candidatures de SES offres) — nécessite une notion d'ownership d'offre.

EMPLACEMENT MVC
    Couche "auth" : sécurité transverse. Reçoit `db` + l'utilisateur courant.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, Role
from app.models.profil import Profil
from app.models.candidature import Candidature


def profil_of_user(db: Session, user_id: int) -> Profil | None:
    """Profil de carrière lié à un compte (None si aucun)."""
    return db.scalar(select(Profil).where(Profil.user_id == user_id))


def _is_global(user: User) -> bool:
    """RH/ADMIN : périmètre global (voit/agit sur tout)."""
    return user.role in (Role.RH, Role.ADMIN)


def is_manager_of_profil(db: Session, manager_user_id: int, profil: Profil) -> bool:
    """Vrai si `profil` est dans l'équipe du manager (compte lié managé par lui)."""
    if profil.user_id is None:
        return False
    linked = db.get(User, profil.user_id)
    return linked is not None and linked.manager_id == manager_user_id


# ------------------------------------------------------------------ Profils

def can_view_profil(db: Session, user: User, profil: Profil) -> bool:
    """Droit de LECTURE du profil complet (identité, aspirations, compétences…)."""
    if _is_global(user):
        return True
    if profil.user_id is not None and profil.user_id == user.id:
        return True                                  # son propre profil
    if user.role == Role.MANAGER and is_manager_of_profil(db, user.id, profil):
        return True                                  # membre de son équipe
    return False


def require_profil_view(db: Session, user: User, profil_id: int) -> Profil:
    """Charge le profil (404 si absent) et vérifie le périmètre de lecture (403)."""
    p = db.get(Profil, profil_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    if not can_view_profil(db, user, p):
        raise HTTPException(status_code=403, detail="Ce profil est hors de votre périmètre.")
    return p


# --------------------------------------------------------------- Candidatures

def require_own_profil_for_candidature(db: Session, user: User, profil_id: int) -> None:
    """Un COLLAB ne peut candidater que pour SON profil (403 sinon). RH/ADMIN libres."""
    if _is_global(user):
        return
    own = profil_of_user(db, user.id)
    if own is None or own.id != profil_id:
        raise HTTPException(
            status_code=403,
            detail="Vous ne pouvez déposer une candidature que pour votre propre profil.")


def can_view_candidature(db: Session, user: User, cand: Candidature) -> bool:
    """Droit de lecture d'une candidature = droit de lecture du profil candidat."""
    if _is_global(user):
        return True
    profil = db.get(Profil, cand.profil_id)
    return profil is not None and can_view_profil(db, user, profil)


def require_candidature_view(db: Session, user: User, candidature_id: int) -> Candidature:
    """Charge la candidature (404 si absente) et vérifie le périmètre (403)."""
    c = db.get(Candidature, candidature_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    if not can_view_candidature(db, user, c):
        raise HTTPException(status_code=403, detail="Cette candidature est hors de votre périmètre.")
    return c


def require_candidature_list_scope(db: Session, user: User,
                                   offre_id: int | None, profil_id: int | None) -> None:
    """Autorise une liste de candidatures selon le périmètre (403 sinon) :
      - RH/ADMIN : tout ;
      - COLLAB   : uniquement ses candidatures (profil_id == son profil) ;
      - MANAGER  : candidats d'une offre (offre_id) OU candidatures d'un profil de
                   son équipe (profil_id).
    """
    if _is_global(user):
        return
    if user.role == Role.COLLAB:
        own = profil_of_user(db, user.id)
        if own is None or profil_id != own.id:
            raise HTTPException(
                status_code=403,
                detail="Filtrez par votre propre profil (profil_id) ou utilisez /api/candidatures/mes.")
        return
    if user.role == Role.MANAGER:
        if profil_id is not None:
            p = db.get(Profil, profil_id)
            if p is None or not can_view_profil(db, user, p):
                raise HTTPException(status_code=403, detail="Ce profil est hors de votre équipe.")
            return
        if offre_id is not None:
            return                                   # revue des candidats d'une offre
        raise HTTPException(
            status_code=403,
            detail="Précisez une offre (offre_id) ou un profil de votre équipe (profil_id).")
    raise HTTPException(status_code=403, detail="Accès non autorisé.")
