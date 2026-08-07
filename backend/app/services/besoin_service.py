#!/usr/bin/env python3
"""
services/besoin_service.py — Workflow BESOIN de recrutement (manager → HRBP → offre).

Le manager exprime un besoin sur un poste et le transmet (notification aux HRBP).
La HRBP valide/refuse, puis PUBLIE l'offre EN CONTINUITÉ : l'offre porte la
« marque » du manager d'origine (`Offre.manager_id`), ce qui lui donne la même
visibilité qu'à la HRBP sur les candidatures. Le besoin est relié à l'offre.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.besoin import BesoinRecrutement, BesoinStatut
from app.models.user import User
from app.models.offre import OffreType, OffreStatut
from app.schemas.besoin import BesoinCreate, BesoinOut, BesoinPublier
from app.schemas.offre import OffreCreate
from app.services import offre_service, notification_service


def _to_out(db: Session, b: BesoinRecrutement) -> BesoinOut:
    mgr = db.get(User, b.manager_user_id)
    out = BesoinOut.model_validate(b)
    out.manager_nom = mgr.name if mgr else None
    return out


def creer_besoin(db: Session, manager_user_id: int, data: BesoinCreate) -> BesoinOut:
    """Le manager exprime un besoin → statut TRANSMIS + notification aux HRBP."""
    b = BesoinRecrutement(
        manager_user_id=manager_user_id, fiche_id=data.fiche_id,
        poste=data.poste.strip(), description=(data.description or "").strip() or None,
        statut=BesoinStatut.TRANSMIS)
    db.add(b)
    db.commit()
    db.refresh(b)
    mgr = db.get(User, manager_user_id)
    notification_service.communiquer_aux_rh(
        db, from_name=(mgr.name if mgr else "Un manager"),
        sujet="Besoin de recrutement",
        message=f"Nouveau besoin de recrutement sur « {b.poste} ». "
                + (b.description or "Sans description."))
    return _to_out(db, b)


def mes_besoins(db: Session, manager_user_id: int) -> list[BesoinOut]:
    rows = db.scalars(select(BesoinRecrutement)
                      .where(BesoinRecrutement.manager_user_id == manager_user_id)
                      .order_by(BesoinRecrutement.id.desc())).all()
    return [_to_out(db, b) for b in rows]


def lister_besoins(db: Session, statut: str | None = None) -> list[BesoinOut]:
    """Vue HRBP : tous les besoins (option filtre statut), les transmis d'abord."""
    stmt = select(BesoinRecrutement).order_by(BesoinRecrutement.id.desc())
    if statut:
        stmt = stmt.where(BesoinRecrutement.statut == statut)
    return [_to_out(db, b) for b in db.scalars(stmt).all()]


def _get(db: Session, besoin_id: int) -> BesoinRecrutement | None:
    return db.get(BesoinRecrutement, besoin_id)


def valider(db: Session, besoin_id: int, hrbp_user_id: int) -> BesoinOut | None:
    b = _get(db, besoin_id)
    if b is None:
        return None
    b.statut = BesoinStatut.VALIDE
    b.hrbp_user_id = hrbp_user_id
    b.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(b)
    notification_service.create_notification(
        db, user_id=b.manager_user_id, titre="Besoin validé",
        texte=f"Votre besoin « {b.poste} » a été validé par la HRBP ; l'offre va être publiée.",
        to_route="manager.offres")
    return _to_out(db, b)


def refuser(db: Session, besoin_id: int, hrbp_user_id: int, motif: str | None) -> BesoinOut | None:
    b = _get(db, besoin_id)
    if b is None:
        return None
    b.statut = BesoinStatut.REFUSE
    b.hrbp_user_id = hrbp_user_id
    b.motif_refus = (motif or "").strip() or None
    b.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(b)
    notification_service.create_notification(
        db, user_id=b.manager_user_id, titre="Besoin non retenu",
        texte=f"Votre besoin « {b.poste} » n'a pas été retenu."
              + (f" Motif : {b.motif_refus}" if b.motif_refus else ""),
        to_route="manager.offres")
    return _to_out(db, b)


def publier(db: Session, besoin_id: int, hrbp_user_id: int, data: BesoinPublier):
    """Publie l'offre EN CONTINUITÉ du besoin : created_by=HRBP, manager_id=manager
    d'origine (visibilité partagée), compétences héritées de la fiche. Renvoie
    (OffreOut, BesoinOut) ou (None, None) si le besoin est introuvable."""
    b = _get(db, besoin_id)
    if b is None:
        return None, None
    offre = offre_service.create_offre(db, OffreCreate(
        titre=(data.titre or b.poste).strip(),
        fiche_id=b.fiche_id, heriter_competences=b.fiche_id is not None,
        type=OffreType.OFFRE_POSTE,
        description=(data.description or b.description),
        localisation=data.localisation,
        statut=OffreStatut.OUVERTE,
        created_by=hrbp_user_id,          # publieur = HRBP
        manager_id=b.manager_user_id,     # « marque » du manager d'origine → visibilité partagée
    ))
    b.offre_id = offre.id
    b.statut = BesoinStatut.PUBLIE
    b.hrbp_user_id = hrbp_user_id
    b.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(b)
    notification_service.create_notification(
        db, user_id=b.manager_user_id, titre="Offre publiée",
        texte=f"L'offre « {offre.titre} » issue de votre besoin est publiée. "
              "Vous pouvez suivre les candidatures.",
        to_route="manager.mesOffres")
    return offre, _to_out(db, b)
