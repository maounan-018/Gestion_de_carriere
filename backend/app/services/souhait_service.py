#!/usr/bin/env python3
"""
services/souhait_service.py — Logique métier des souhaits d'évolution.

RÔLE
    Le collaborateur gère SES souhaits (via son `Profil`) et peut les POUSSER au
    manager. Le manager consulte les souhaits poussés par les membres de son équipe
    (`souhaits_recus`). L'appartenance ligne-à-ligne (ownership) est vérifiée ici :
    un souhait n'est éditable que par le propriétaire de son profil.

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import Profil
from app.models.souhait import Souhait, SouhaitStatut
from app.models.user import User
from app.schemas.souhait import SouhaitCreate, SouhaitUpdate, SouhaitOut, SouhaitRecuOut
from app.auth import ownership
from app.services import notification_events

# Statuts « poussés » visibles du manager.
_STATUTS_POUSSES = {SouhaitStatut.POUSSE, SouhaitStatut.EN_DISCUSSION,
                    SouhaitStatut.ACCORDE, SouhaitStatut.REFUSE}


def profil_of_user(db: Session, user_id: int) -> Profil | None:
    """Profil de carrière lié à un compte (None si le compte n'a pas de profil)."""
    return db.scalar(select(Profil).where(Profil.user_id == user_id))


def list_souhaits(db: Session, profil_id: int) -> list[SouhaitOut]:
    stmt = select(Souhait).where(Souhait.profil_id == profil_id).order_by(Souhait.id.desc())
    return [SouhaitOut.model_validate(s) for s in db.scalars(stmt).all()]


def create_souhait(db: Session, profil_id: int, data: SouhaitCreate) -> SouhaitOut:
    s = Souhait(
        profil_id=profil_id, titre=data.titre, kind=data.kind, horizon=data.horizon,
        description=data.description, pushed=data.pushed,
        statut=SouhaitStatut.POUSSE if data.pushed else SouhaitStatut.BROUILLON,
    )
    db.add(s)
    if data.pushed:  # créé directement « poussé » -> notifie le manager (atomique)
        profil = db.get(Profil, profil_id)
        if profil is not None:
            notification_events.on_souhait_pousse(
                db, s, profil, ownership.manager_user_id_of_profil(db, profil))
    db.commit()
    db.refresh(s)
    return SouhaitOut.model_validate(s)


def get_souhait(db: Session, souhait_id: int) -> Souhait | None:
    return db.get(Souhait, souhait_id)


def update_souhait(db: Session, souhait_id: int, data: SouhaitUpdate) -> SouhaitOut | None:
    """Met à jour un souhait (l'ownership est vérifié par l'appelant/controller).
    Passer `pushed=True` bascule un brouillon en « poussé »."""
    s = db.get(Souhait, souhait_id)
    if s is None:
        return None
    prev_statut = s.statut
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(s, field, value)
    # Cohérence statut/pushed : pousser un brouillon le fait passer « poussé ».
    devient_pousse = changes.get("pushed") is True and prev_statut == SouhaitStatut.BROUILLON
    if devient_pousse:
        s.statut = SouhaitStatut.POUSSE
    est_decide = "statut" in changes and changes["statut"] in (SouhaitStatut.ACCORDE,
                                                               SouhaitStatut.REFUSE)
    if est_decide:
        s.decided_at = datetime.now(timezone.utc)
    # Notifications (atomiques) : poussée -> manager ; décision -> collaborateur.
    if devient_pousse or est_decide:
        profil = db.get(Profil, s.profil_id)
        if profil is not None:
            if devient_pousse:
                notification_events.on_souhait_pousse(
                    db, s, profil, ownership.manager_user_id_of_profil(db, profil))
            if est_decide:
                notification_events.on_souhait_decide(db, s, profil)
    db.commit()
    db.refresh(s)
    return SouhaitOut.model_validate(s)


def list_recus_for_manager(db: Session, manager_user_id: int) -> list[SouhaitRecuOut]:
    """Souhaits POUSSÉS par les collaborateurs dont le manager est `manager_user_id`.
    Jointure Souhait → Profil → User(profil.user_id), filtre User.manager_id."""
    stmt = (
        select(Souhait, Profil)
        .join(Profil, Profil.id == Souhait.profil_id)
        .join(User, User.id == Profil.user_id)
        .where(User.manager_id == manager_user_id, Souhait.statut.in_(_STATUTS_POUSSES))
        .order_by(Souhait.created_at.desc(), Souhait.id.desc())
    )
    out: list[SouhaitRecuOut] = []
    for souhait, profil in db.execute(stmt).all():
        out.append(SouhaitRecuOut(
            **SouhaitOut.model_validate(souhait).model_dump(),
            membre_nom=profil.nom, membre_prenom=profil.prenom,
            membre_matricule=profil.matricule,
        ))
    return out
