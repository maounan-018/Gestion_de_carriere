#!/usr/bin/env python3
"""
services/offre_service.py — Logique métier d'une Offre (CRUD + dérivation Fiche).

RÔLE
    Crée, lit, met à jour et liste les offres (offre de poste / mission / projet /
    gig) et leurs ATTENDUS overridables (`OffreCompetence`). À la création avec une
    `fiche_id`, copie les compétences de la Fiche de référence en attendus
    (`source="fiche"`, importance par défaut « essentielle », niveau à préciser),
    SANS jamais modifier la Fiche. Les attendus sont ensuite éditables au niveau
    de l'offre (ajout, override, retrait).

    Renvoie toujours des schémas Pydantic (jamais d'ORM nu), comme profil_service.

EMPLACEMENT MVC
    Couche "services" : règles métier, transactions. Reçoit `db` en paramètre.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.models.fiche import FicheCompetence
from app.models.fiche import Fiche
from app.models.offre import Offre, OffreCompetence, OffreStatut
from app.models.profil import Profil
from app.models.user import User
from app.models.candidature import Candidature, CandidatureStatut
from app.schemas.offre import (OffreCreate, OffreUpdate, OffreOut,
                               OffreCompetenceIn, OffreCompetenceOut,
                               OffreCompetenceUpdate, OffreCompatOut,
                               OffreCandidatOut, RhOffreOut, CandidatOffreActiveOut,
                               VacancyOut, VacancyRecoOut)
from app.services import candidature_service

# Seuil de compatibilité (%) au-delà duquel un candidat est compté « compatible ».
_SEUIL_COMPAT = 50

# Statuts qui, à l'entrée, posent automatiquement une date si elle manque.
_STATUTS_OUVERTURE = {OffreStatut.OUVERTE}
_STATUTS_CLOTURE = {OffreStatut.POURVUE, OffreStatut.FERMEE, OffreStatut.ANNULEE}


def _to_out(db: Session, o: Offre) -> OffreOut:
    """Assemble un OffreOut : l'offre + ses attendus (requête explicite)."""
    comps = db.scalars(
        select(OffreCompetence)
        .where(OffreCompetence.offre_id == o.id)
        .order_by(OffreCompetence.id)
    ).all()
    out = OffreOut.model_validate(o)
    out.competences = [OffreCompetenceOut.model_validate(c) for c in comps]
    return out


def _libelles(evaluation_json: str | None, cle: str) -> list[str]:
    """Extrait les libellés de compétences (`couvertes` ou `ecarts`) du snapshot
    d'évaluation persisté sur la candidature. Tolérant : [] si illisible."""
    if not evaluation_json:
        return []
    try:
        data = json.loads(evaluation_json)
        return [x.get("competence") for x in data.get(cle, []) if x.get("competence")]
    except Exception:  # noqa: BLE001 — snapshot corrompu : on renvoie une liste vide
        return []


def list_candidats_offre(db: Session, offre_id: int) -> list[OffreCandidatOut]:
    """Candidats d'une offre (écran RH revue) : jointure candidature ↔ profil,
    triés par score décroissant ; couvertes/écarts issus du snapshot d'évaluation."""
    rows = db.execute(
        select(Candidature, Profil)
        .join(Profil, Profil.id == Candidature.profil_id)
        .where(Candidature.offre_id == offre_id)
        .order_by(Candidature.score.desc().nulls_last(), Candidature.id)
    ).all()
    return [
        OffreCandidatOut(
            profil_id=p.id, candidature_id=c.id, nom=p.nom, prenom=p.prenom,
            poste_actuel=p.poste_actuel, departement_key=p.departement_key,
            score=c.score, statut=c.statut, cv_filename=p.cv_filename,
            couvertes=_libelles(c.evaluation_json, "couvertes"),
            ecarts=_libelles(c.evaluation_json, "ecarts"),
        )
        for c, p in rows
    ]


def rh_offres(db: Session, *, created_by: int | None = None) -> list[RhOffreOut]:
    """Liste des offres avec statistiques de candidatures (total, compatibles
    au-dessus du seuil, candidat retenu). Si `created_by` est fourni, ne renvoie
    que les offres PUBLIÉES PAR cet utilisateur (écran « Mes offres publiées »)."""
    stmt = select(Offre).order_by(Offre.id.desc())
    if created_by is not None:
        stmt = stmt.where(Offre.created_by == created_by)
    offres = db.scalars(stmt).all()
    if not offres:
        return []

    # Agrégats candidatures PAR OFFRE en UNE requête (total + compatibles) au lieu
    # d'une requête par offre (N+1). NULL score -> compté comme non compatible.
    stats: dict[int, tuple[int, int]] = {}
    for oid, total, compat in db.execute(
            select(Candidature.offre_id, func.count(Candidature.id),
                   func.sum(case((Candidature.score >= _SEUIL_COMPAT, 1), else_=0)))
            .group_by(Candidature.offre_id)).all():
        stats[oid] = (total or 0, int(compat or 0))

    # Candidat retenu par offre en UNE requête (le 1er retenu rencontré par offre).
    retenus: dict[int, str] = {}
    for oid, nom, prenom in db.execute(
            select(Candidature.offre_id, Profil.nom, Profil.prenom)
            .join(Profil, Profil.id == Candidature.profil_id)
            .where(Candidature.statut == CandidatureStatut.RETENUE)).all():
        retenus.setdefault(oid, f"{prenom or ''} {nom}".strip())

    out: list[RhOffreOut] = []
    for o in offres:
        total, compat = stats.get(o.id, (0, 0))
        out.append(RhOffreOut(
            id=o.id, titre=o.titre, type=o.type, departement_key=o.departement_key,
            perimetre_bmci=o.perimetre_bmci, statut=o.statut,
            candidats_total=total, candidats_compatibles=compat,
            retenu_nom=retenus.get(o.id),
        ))
    return out


def candidats_offres_actives(db: Session, user_id: int) -> list[CandidatOffreActiveOut]:
    """Candidats des offres ENCORE EN COURS (non clôturées / non retirées) publiées
    par `user_id`. Liste aplatie (une ligne par candidature), triée par offre puis
    par score décroissant. Alimente le KPI « Candidatures » du tableau de bord."""
    rows = db.execute(
        select(Candidature, Profil, Offre)
        .join(Profil, Profil.id == Candidature.profil_id)
        .join(Offre, Offre.id == Candidature.offre_id)
        .where(Offre.created_by == user_id, Offre.statut.not_in(_STATUTS_CLOTURE))
        .order_by(Offre.id.desc(), Candidature.score.desc().nulls_last(), Candidature.id)
    ).all()
    return [
        CandidatOffreActiveOut(
            offre_id=o.id, offre_titre=o.titre, offre_type=o.type, offre_statut=o.statut,
            profil_id=p.id, candidature_id=c.id, nom=p.nom, prenom=p.prenom,
            poste_actuel=p.poste_actuel, score=c.score, statut=c.statut,
        )
        for c, p, o in rows
    ]


def vacancies_for_manager(db: Session, manager_user_id: int, *, top: int = 6) -> list[VacancyOut]:
    """Postes à pourvoir de l'équipe d'un manager (offres qu'il a poussées) +
    profils internes recommandés (MATCHING INVERSE). Pour chaque poste, on évalue
    chaque membre de l'équipe (profils rattachés à `manager_user_id`, cohérent avec
    l'écran Équipe) contre les attendus de l'offre, via le même évaluateur que les
    candidatures, et on classe par score décroissant."""
    # Rattachement par Profil.manager_id (les profils candidats n'ont pas de compte,
    # donc un join via User.manager_id les exclurait — cf. écran Équipe / getTeam).
    team = db.scalars(
        select(Profil).where(Profil.manager_id == manager_user_id)
    ).all()
    offres = db.scalars(
        select(Offre).where(Offre.created_by == manager_user_id).order_by(Offre.id.desc())
    ).all()

    out: list[VacancyOut] = []
    for o in offres:
        recos: list[VacancyRecoOut] = []
        for p in team:
            ev = candidature_service.evaluer(db, o.id, p.id)
            recos.append(VacancyRecoOut(
                profil_id=p.id, nom=p.nom, prenom=p.prenom, poste_actuel=p.poste_actuel,
                score=ev.score,
                matched=[c.competence for c in ev.couvertes],
                gaps=[e.competence for e in ev.ecarts]))
        recos.sort(key=lambda r: r.score, reverse=True)
        out.append(VacancyOut(
            id=o.id, titre=o.titre, type=o.type, departement_key=o.departement_key,
            perimetre_bmci=o.perimetre_bmci, description=o.description, statut=o.statut,
            created_at=o.created_at, recos=recos[:top]))
    return out


def _add_competences(db: Session, offre_id: int, comps: list[OffreCompetenceIn]) -> None:
    for c in comps:
        db.add(OffreCompetence(
            offre_id=offre_id, libelle=c.libelle, categorie=c.categorie,
            skill_id=c.skill_id, skill_label_fr=c.skill_label_fr,
            importance=c.importance, niveau_requis=c.niveau_requis, source=c.source,
        ))


def _heriter_de_fiche(db: Session, offre_id: int, fiche_id: int) -> None:
    """Copie les compétences de la Fiche de référence en attendus overridables.
    La Fiche n'est PAS modifiée ; importance/niveau prennent des défauts éditables."""
    fcomps = db.scalars(
        select(FicheCompetence)
        .where(FicheCompetence.fiche_id == fiche_id)
        .order_by(FicheCompetence.id)
    ).all()
    for fc in fcomps:
        db.add(OffreCompetence(
            offre_id=offre_id, libelle=fc.libelle, categorie=fc.categorie,
            skill_id=fc.skill_id, skill_label_fr=fc.skill_label_fr,
            rerank_score=fc.rerank_score,
            importance="essentielle", niveau_requis=None, source="fiche",
        ))


def create_offre(db: Session, data: OffreCreate) -> OffreOut:
    """Crée une offre. Si `fiche_id` est fourni, la Fiche doit exister ; ses
    compétences sont héritées comme attendus (si `heriter_competences`). Lève
    ValueError si la Fiche référencée est introuvable."""
    if data.fiche_id is not None and db.get(Fiche, data.fiche_id) is None:
        raise ValueError(f"Fiche de référence {data.fiche_id} introuvable.")

    o = Offre(
        fiche_id=data.fiche_id, type=data.type, titre=data.titre,
        description=data.description, localisation=data.localisation, duree=data.duree,
        perimetre_bmci=data.perimetre_bmci,
        departement_key=data.departement_key, statut=data.statut,
        created_by=data.created_by, manager_id=data.manager_id,
        date_ouverture=data.date_ouverture, date_cloture=data.date_cloture,
        synthetique=data.synthetique,
    )
    # Dates cohérentes avec le statut initial.
    _appliquer_dates_statut(o, data.statut)
    db.add(o)
    db.flush()  # -> o.id

    if data.fiche_id is not None and data.heriter_competences:
        _heriter_de_fiche(db, o.id, data.fiche_id)
    _add_competences(db, o.id, data.competences)

    db.commit()
    db.refresh(o)
    return _to_out(db, o)


def get_offre(db: Session, offre_id: int) -> OffreOut | None:
    o = db.get(Offre, offre_id)
    return _to_out(db, o) if o else None


def list_compatibles(db: Session, profil_id: int | None) -> list[OffreCompatOut]:
    """Offres enrichies d'un % de compatibilité POUR le profil donné (déterministe,
    via candidature_service.evaluer — pas d'Ollama). Triées par adéquation
    décroissante. Si profil_id est None, renvoie les offres sans score."""
    offres = db.scalars(select(Offre).order_by(Offre.id.desc())).all()
    if not offres:
        return []
    # Compétences de TOUTES les offres en UNE requête (au lieu d'une par offre),
    # regroupées par offre puis tronquées à 8 pour l'affichage.
    comps_par_offre: dict[int, list[OffreCompetence]] = {}
    for c in db.scalars(
            select(OffreCompetence).where(OffreCompetence.offre_id.in_([o.id for o in offres]))
            .order_by(OffreCompetence.offre_id, OffreCompetence.id)).all():
        comps_par_offre.setdefault(c.offre_id, []).append(c)

    out: list[OffreCompatOut] = []
    for o in offres:
        comps = comps_par_offre.get(o.id, [])[:8]
        score = couv = ecr = None
        if profil_id is not None:
            ev = candidature_service.evaluer(db, o.id, profil_id)
            score, couv, ecr = ev.score, len(ev.couvertes), len(ev.ecarts)
        out.append(OffreCompatOut(
            id=o.id, type=o.type, titre=o.titre, description=o.description,
            perimetre_bmci=o.perimetre_bmci, departement_key=o.departement_key,
            statut=o.statut, competences=[c.skill_label_fr or c.libelle for c in comps],
            score_compat=score, couvertes=couv or 0, ecarts=ecr or 0,
        ))
    out.sort(key=lambda x: x.score_compat if x.score_compat is not None else -1, reverse=True)
    return out


def list_compatibles_for_user(db: Session, user_id: int) -> list[OffreCompatOut]:
    """Compatibilité des offres pour le profil LIÉ au compte connecté (ou sans
    score si le compte n'a pas de profil)."""
    p = db.scalar(select(Profil).where(Profil.user_id == user_id))
    return list_compatibles(db, p.id if p else None)


def list_offres(db: Session, *, statut: str | None = None, type: str | None = None,
                departement_key: str | None = None, fiche_id: int | None = None,
                synthetique: bool | None = None, limit: int = 50,
                offset: int = 0) -> list[OffreOut]:
    """Liste paginée, filtrable (statut, type, département, fiche, nature)."""
    stmt = select(Offre).order_by(Offre.id.desc())
    if statut is not None:
        stmt = stmt.where(Offre.statut == statut)
    if type is not None:
        stmt = stmt.where(Offre.type == type)
    if departement_key is not None:
        stmt = stmt.where(Offre.departement_key == departement_key)
    if fiche_id is not None:
        stmt = stmt.where(Offre.fiche_id == fiche_id)
    if synthetique is not None:
        stmt = stmt.where(Offre.synthetique == synthetique)
    stmt = stmt.limit(min(max(limit, 1), 200)).offset(max(offset, 0))
    return [_to_out(db, o) for o in db.scalars(stmt).all()]


def _appliquer_dates_statut(o: Offre, statut: str | None) -> None:
    """Pose date_ouverture/date_cloture selon le statut, sans écraser l'existant."""
    if statut in _STATUTS_OUVERTURE and o.date_ouverture is None:
        o.date_ouverture = datetime.now(timezone.utc)
    if statut in _STATUTS_CLOTURE and o.date_cloture is None:
        o.date_cloture = datetime.now(timezone.utc)


def update_offre(db: Session, offre_id: int, data: OffreUpdate) -> OffreOut | None:
    """Mise à jour partielle de l'offre (jamais la Fiche). None si introuvable.
    Une transition de statut pose automatiquement la date correspondante."""
    o = db.get(Offre, offre_id)
    if not o:
        return None
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(o, field, value)
    if "statut" in changes:
        _appliquer_dates_statut(o, changes["statut"])
    db.commit()
    db.refresh(o)
    return _to_out(db, o)


def add_competences(db: Session, offre_id: int,
                    comps: list[OffreCompetenceIn]) -> OffreOut | None:
    """Ajoute des attendus à une offre existante. None si introuvable."""
    o = db.get(Offre, offre_id)
    if not o:
        return None
    _add_competences(db, offre_id, comps)
    db.commit()
    return _to_out(db, o)


def update_competence(db: Session, offre_id: int, comp_id: int,
                      data: OffreCompetenceUpdate) -> OffreOut | None:
    """Override un attendu au niveau de l'offre (importance, niveau, libellé…).
    None si l'offre ou l'attendu (rattaché à cette offre) est introuvable."""
    o = db.get(Offre, offre_id)
    if not o:
        return None
    comp = db.get(OffreCompetence, comp_id)
    if comp is None or comp.offre_id != offre_id:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(comp, field, value)
    db.commit()
    return _to_out(db, o)


def delete_competence(db: Session, offre_id: int, comp_id: int) -> OffreOut | None:
    """Retire un attendu de l'offre. None si offre/attendu introuvable."""
    o = db.get(Offre, offre_id)
    if not o:
        return None
    comp = db.get(OffreCompetence, comp_id)
    if comp is None or comp.offre_id != offre_id:
        return None
    db.delete(comp)
    db.commit()
    return _to_out(db, o)


def mission_participants(db: Session, offre_id: int) -> list[dict]:
    """Participants RETENUS d'une offre (candidature statut=retenue) avec nom et
    poste — pour l'écran d'évaluation de mission (Workstream C)."""
    rows = db.execute(
        select(Profil.id, Profil.prenom, Profil.nom, Profil.poste_actuel)
        .join(Candidature, Candidature.profil_id == Profil.id)
        .where(Candidature.offre_id == offre_id,
               Candidature.statut == CandidatureStatut.RETENUE)
        .order_by(Profil.nom)
    ).all()
    return [
        {"profil_id": pid,
         "nom": f"{(prenom or '').strip()} {nom}".strip(),
         "poste_actuel": poste}
        for (pid, prenom, nom, poste) in rows
    ]
