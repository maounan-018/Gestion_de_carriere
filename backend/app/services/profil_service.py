#!/usr/bin/env python3
"""
services/profil_service.py — Logique métier du Profil collaborateur (CRUD).

RÔLE
    Crée, lit, met à jour et liste les profils et leurs compétences détenues.
    Les compétences peuvent plus tard être ancrées au graphe (skill_id via
    skill_search) comme pour les fiches ; on stocke ici le déclaratif brut +
    l'éventuel ancrage. Toute la couche renvoie des schémas Pydantic (jamais
    d'objets ORM nus), à l'image de skill_matching_service.

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.profil import Profil, ProfilCompetence, CompetenceSource
from app.models.user import User
from app.models.carriere import ProfilStation, PeerReview
from app.services import occupation_service
from app.schemas.profil import (ProfilCreate, ProfilUpdate, ProfilSelfUpdate, ProfilOut,
                                 ProfilCompetenceIn, ProfilCompetenceOut, AnnuaireEntry)
from app.schemas.carriere import (ProfilCarriereOut, StationOut, PeerReviewOut,
                                  SkillNiveauOut)


def _to_out(db: Session, p: Profil) -> ProfilOut:
    """Assemble un ProfilOut : le profil + ses compétences (requête explicite,
    le repo n'utilise pas de relationships ORM)."""
    comps = db.scalars(
        select(ProfilCompetence)
        .where(ProfilCompetence.profil_id == p.id)
        .order_by(ProfilCompetence.id)
    ).all()
    out = ProfilOut.model_validate(p)
    out.competences = [ProfilCompetenceOut.model_validate(c) for c in comps]
    return out


def _add_competences(db: Session, profil_id: int, comps: list[ProfilCompetenceIn]) -> None:
    for c in comps:
        db.add(ProfilCompetence(
            profil_id=profil_id, libelle=c.libelle, categorie=c.categorie,
            niveau=c.niveau, source=c.source,
        ))


def create_profil(db: Session, data: ProfilCreate) -> ProfilOut:
    """Crée un profil (+ ses compétences initiales) et renvoie sa vue complète."""
    p = Profil(
        nom=data.nom, prenom=data.prenom, matricule=data.matricule,
        poste_actuel=data.poste_actuel, departement_key=data.departement_key,
        aspirations=data.aspirations, user_id=data.user_id,
        manager_id=data.manager_id, synthetique=data.synthetique,
    )
    db.add(p)
    db.flush()  # -> p.id
    _add_competences(db, p.id, data.competences)
    db.commit()
    db.refresh(p)
    return _to_out(db, p)


def get_profil(db: Session, profil_id: int) -> ProfilOut | None:
    """Renvoie le profil et ses compétences, ou None s'il n'existe pas."""
    p = db.get(Profil, profil_id)
    return _to_out(db, p) if p else None


def update_self(db: Session, user_id: int, data: ProfilSelfUpdate) -> ProfilOut | None:
    """Auto-édition : l'utilisateur met à jour SON profil lié (champs self-safe
    uniquement, cf. ProfilSelfUpdate — jamais département/manager). None si le
    compte n'a pas de profil de carrière."""
    p = db.scalar(select(Profil).where(Profil.user_id == user_id))
    if p is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return _to_out(db, p)


def list_profils(db: Session, *, departement_key: str | None = None,
                 synthetique: bool | None = None, manager_id: int | None = None,
                 limit: int = 50, offset: int = 0) -> list[ProfilOut]:
    """Liste paginée, filtrable par département, par nature (persona vs réel) et
    par manager (l'ÉQUIPE d'un manager = profils dont le compte a ce manager)."""
    stmt = select(Profil).order_by(Profil.id)
    if departement_key is not None:
        stmt = stmt.where(Profil.departement_key == departement_key)
    if synthetique is not None:
        stmt = stmt.where(Profil.synthetique == synthetique)
    if manager_id is not None:
        stmt = stmt.join(User, User.id == Profil.user_id).where(User.manager_id == manager_id)
    stmt = stmt.limit(min(max(limit, 1), 200)).offset(max(offset, 0))
    return [_to_out(db, p) for p in db.scalars(stmt).all()]


def list_annuaire(db: Session, *, departement_key: str | None = None,
                  limit: int = 200, offset: int = 0) -> list[AnnuaireEntry]:
    """Répertoire LIMITÉ (sans champ sensible) de tous les profils — accessible à
    tout utilisateur authentifié (y compris COLLAB). Compétences = libellés seuls."""
    stmt = select(Profil).order_by(Profil.nom, Profil.prenom)
    if departement_key is not None:
        stmt = stmt.where(Profil.departement_key == departement_key)
    stmt = stmt.limit(min(max(limit, 1), 500)).offset(max(offset, 0))
    entries: list[AnnuaireEntry] = []
    for p in db.scalars(stmt).all():
        comps = db.scalars(
            select(ProfilCompetence).where(ProfilCompetence.profil_id == p.id)
            .order_by(ProfilCompetence.id).limit(8)
        ).all()
        entries.append(AnnuaireEntry(
            id=p.id, nom=p.nom, prenom=p.prenom, poste_actuel=p.poste_actuel,
            departement_key=p.departement_key,
            competences=[c.skill_label_fr or c.libelle for c in comps],
        ))
    return entries


def get_carriere_for_user(db: Session, user_id: int) -> ProfilCarriereOut | None:
    """Vue carrière du profil LIÉ à un compte (pour « mon profil » sans connaître
    l'id du profil). None si le compte n'a pas de profil de carrière."""
    p = db.scalar(select(Profil).where(Profil.user_id == user_id))
    return get_carriere(db, p.id) if p else None


def get_carriere(db: Session, profil_id: int) -> ProfilCarriereOut | None:
    """Vue « carrière » enrichie : identité, aspirations, compétences (niveau),
    jalons de progression et avis des pairs. None si le profil n'existe pas."""
    p = db.get(Profil, profil_id)
    if p is None:
        return None
    comps = db.scalars(
        select(ProfilCompetence).where(ProfilCompetence.profil_id == profil_id)
        .order_by(ProfilCompetence.id)).all()
    stations = db.scalars(
        select(ProfilStation).where(ProfilStation.profil_id == profil_id)
        .order_by(ProfilStation.ordre, ProfilStation.id)).all()
    avis = db.scalars(
        select(PeerReview).where(PeerReview.profil_id == profil_id)
        .order_by(PeerReview.id)).all()
    return ProfilCarriereOut(
        profil_id=p.id, nom=p.nom, prenom=p.prenom, poste_actuel=p.poste_actuel,
        departement_key=p.departement_key, aspirations=p.aspirations,
        competences=[SkillNiveauOut.model_validate(c) for c in comps],
        stations=[StationOut.model_validate(s) for s in stations],
        avis_pairs=[PeerReviewOut.model_validate(a) for a in avis],
    )


def update_profil(db: Session, profil_id: int, data: ProfilUpdate) -> ProfilOut | None:
    """Mise à jour partielle (champs non-None uniquement). None si introuvable."""
    p = db.get(Profil, profil_id)
    if not p:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return _to_out(db, p)


def add_competences(db: Session, profil_id: int,
                    comps: list[ProfilCompetenceIn]) -> ProfilOut | None:
    """Ajoute des compétences détenues à un profil existant. None si introuvable."""
    p = db.get(Profil, profil_id)
    if not p:
        return None
    _add_competences(db, profil_id, comps)
    db.commit()
    return _to_out(db, p)


def passerelles_mobilite(db: Session, profil_id: int, *, k: int = 5) -> list[dict] | None:
    """Passerelles de mobilité d'un profil : métiers du référentiel (ESCO/O*NET) qui
    mobilisent le plus ses compétences détenues ANCRÉES au graphe (skill_id). Exclut
    son poste actuel. None si le profil est introuvable ; [] si compétences non ancrées."""
    p = db.get(Profil, profil_id)
    if p is None:
        return None
    skill_ids = list({sid for (sid,) in db.execute(
        select(ProfilCompetence.skill_id).where(
            ProfilCompetence.profil_id == profil_id,
            ProfilCompetence.skill_id.isnot(None))).all()})
    exclude = {p.poste_actuel} if p.poste_actuel else set()
    return occupation_service.suggest_occupations(db, skill_ids, k=k, exclude_labels=exclude)


def enregistrer_competences_extraites(db: Session, profil_id: int, comps: list[dict],
                                      source: str, *, remplacer: bool = True) -> ProfilOut | None:
    """Persiste des compétences DÉTENUES issues d'une extraction (CV, évaluation…),
    avec leur ancrage graphe (skill_id/skill_label_fr), sous la provenance `source`.
    `comps` = dicts {libelle, categorie, niveau, skill_id, skill_label_fr}. Si
    `remplacer`, purge d'abord les compétences de CETTE MÊME source (ré-extraction
    idempotente, sans toucher aux autres provenances). None si profil introuvable."""
    p = db.get(Profil, profil_id)
    if not p:
        return None
    if remplacer:
        db.execute(delete(ProfilCompetence).where(
            ProfilCompetence.profil_id == profil_id,
            ProfilCompetence.source == source))
    for c in comps:
        db.add(ProfilCompetence(
            profil_id=profil_id, libelle=c["libelle"], categorie=c.get("categorie"),
            niveau=c.get("niveau"), skill_id=c.get("skill_id"),
            skill_label_fr=c.get("skill_label_fr"), source=source))
    db.commit()
    return _to_out(db, p)
