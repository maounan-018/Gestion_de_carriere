#!/usr/bin/env python3
"""
services/dashboard_service.py — Agrégations pour les tableaux de bord RH & manager.

RÔLE
    Calcule à la volée, depuis les données existantes (profils, compétences
    détenues, offres, candidatures, souhaits), les indicateurs et cartographies des
    espaces RH et manager. Aucune table dédiée : ce sont des VUES calculées.

    - `kpis_rh` / `kpis_manager` : compteurs clés (effectif, offres, candidatures…).
    - `cartographie` : par département — effectif, niveau moyen, compétences phares.
    - `hauts_potentiels` : profils au niveau moyen le plus élevé (proxy de potentiel).

EMPLACEMENT MVC
    Couche "services" : lecture/agrégation. Reçoit `db` en paramètre.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.profil import Profil, ProfilCompetence
from app.models.offre import Offre, OffreStatut
from app.models.candidature import Candidature
from app.models.souhait import Souhait
from app.models.user import User
from app.models.formation import Formation
from app.models.entretien import Entretien, EntretienType, EntretienStatut
from app.schemas.dashboard import (KpiItem, CartoDepartement, CartoTopCompetence,
                                    HautPotentielItem, VeilleItem, AlerteItem)


def _count(db: Session, stmt) -> int:
    return db.scalar(select(func.count()).select_from(stmt.subquery())) or 0


# --------------------------------------------------------------------- KPIs
def kpis_rh(db: Session) -> list[KpiItem]:
    effectif = _count(db, select(Profil.id))
    offres_ouvertes = _count(db, select(Offre.id).where(Offre.statut == OffreStatut.OUVERTE))
    candidatures = _count(db, select(Candidature.id))
    competences = _count(db, select(ProfilCompetence.libelle).distinct())
    formations = _count(db, select(Formation.id))
    return [
        KpiItem(key="effectif", value=effectif, label="Profils cartographiés"),
        KpiItem(key="offres_ouvertes", value=offres_ouvertes, label="Offres ouvertes"),
        KpiItem(key="candidatures", value=candidatures, label="Candidatures"),
        KpiItem(key="competences", value=competences, label="Compétences distinctes"),
        KpiItem(key="formations", value=formations, label="Formations au catalogue"),
    ]


def kpis_manager(db: Session, manager_user_id: int) -> list[KpiItem]:
    # Équipe = profils dont le compte a ce manager.
    equipe = _count(
        db, select(Profil.id).join(User, User.id == Profil.user_id)
        .where(User.manager_id == manager_user_id))
    mes_offres_ids = select(Offre.id).where(Offre.created_by == manager_user_id)
    offres = _count(db, mes_offres_ids)
    candidatures = _count(
        db, select(Candidature.id).where(Candidature.offre_id.in_(mes_offres_ids)))
    souhaits = _count(
        db, select(Souhait.id).join(Profil, Profil.id == Souhait.profil_id)
        .join(User, User.id == Profil.user_id)
        .where(User.manager_id == manager_user_id, Souhait.pushed.is_(True)))
    return [
        KpiItem(key="equipe", value=equipe, label="Membres de l'équipe"),
        KpiItem(key="offres", value=offres, label="Offres publiées"),
        KpiItem(key="candidatures", value=candidatures, label="Candidatures reçues"),
        KpiItem(key="souhaits", value=souhaits, label="Souhaits reçus"),
    ]


# ------------------------------------------------------------- Cartographie
def cartographie(db: Session) -> list[CartoDepartement]:
    """Cartographie des compétences par département (effectif, niveau moyen,
    compétences les plus répandues)."""
    # Effectif par département.
    effectifs = dict(db.execute(
        select(Profil.departement_key, func.count(Profil.id))
        .group_by(Profil.departement_key)).all())

    # Niveau moyen + nb de compétences distinctes par département.
    niveau_rows = db.execute(
        select(Profil.departement_key, func.avg(ProfilCompetence.niveau),
               func.count(func.distinct(ProfilCompetence.libelle)))
        .join(ProfilCompetence, ProfilCompetence.profil_id == Profil.id)
        .group_by(Profil.departement_key)).all()
    niveaux = {k: (moy, ncomp) for k, moy, ncomp in niveau_rows}

    # Compétences phares (top 5) par département : nb de profils la détenant + niveau moyen.
    top_rows = db.execute(
        select(Profil.departement_key, ProfilCompetence.libelle,
               func.count(func.distinct(ProfilCompetence.profil_id)),
               func.avg(ProfilCompetence.niveau))
        .join(ProfilCompetence, ProfilCompetence.profil_id == Profil.id)
        .group_by(Profil.departement_key, ProfilCompetence.libelle)
        .order_by(Profil.departement_key,
                  func.count(func.distinct(ProfilCompetence.profil_id)).desc())).all()
    tops: dict[str, list[CartoTopCompetence]] = {}
    for dept, libelle, eff, moy in top_rows:
        bucket = tops.setdefault(dept, [])
        if len(bucket) < 5:
            bucket.append(CartoTopCompetence(
                libelle=libelle, effectif=eff,
                niveau_moyen=round(moy, 2) if moy is not None else None))

    out: list[CartoDepartement] = []
    for dept, eff in sorted(effectifs.items(), key=lambda kv: (kv[0] or "")):
        if dept is None:
            continue
        moy, ncomp = niveaux.get(dept, (None, 0))
        out.append(CartoDepartement(
            departement_key=dept, effectif=eff,
            niveau_moyen=round(moy, 2) if moy is not None else None,
            nb_competences=ncomp or 0, top_competences=tops.get(dept, [])))
    return out


# --------------------------------------------------------- Hauts potentiels
def hauts_potentiels(db: Session, *, limit: int = 10) -> list[HautPotentielItem]:
    """Profils au niveau moyen de compétences le plus élevé (proxy de potentiel).
    Ne considère que les profils ayant au moins 2 compétences niveautées."""
    rows = db.execute(
        select(Profil, func.avg(ProfilCompetence.niveau),
               func.count(ProfilCompetence.id))
        .join(ProfilCompetence, ProfilCompetence.profil_id == Profil.id)
        .where(ProfilCompetence.niveau.isnot(None))
        .group_by(Profil.id)
        .having(func.count(ProfilCompetence.id) >= 2)
        .order_by(func.avg(ProfilCompetence.niveau).desc())
        .limit(min(max(limit, 1), 50))).all()
    out: list[HautPotentielItem] = []
    for profil, moy, ncomp in rows:
        out.append(HautPotentielItem(
            profil_id=profil.id, nom=profil.nom, prenom=profil.prenom,
            poste_actuel=profil.poste_actuel, departement_key=profil.departement_key,
            score=round((moy or 0) * 20), nb_competences=ncomp,
            niveau_moyen=round(moy, 2) if moy is not None else None))
    return out


# ---------------------------------------------------------- Veille entretiens
def veille(db: Session) -> list[VeilleItem]:
    """Suivi des entretiens par type : réalisés / planifiés / en retard."""
    rows = db.execute(
        select(Entretien.type, Entretien.statut, func.count())
        .group_by(Entretien.type, Entretien.statut)).all()
    agg: dict[str, dict[str, int]] = {}
    for type_, statut, n in rows:
        agg.setdefault(type_, {})[statut] = n
    plan = [(EntretienType.ANNUEL, "annuels", "Entretiens annuels (managers)"),
            (EntretienType.RH, "rh", "Entretiens RH ↔ collaborateur")]
    out: list[VeilleItem] = []
    for type_, key, label in plan:
        a = agg.get(type_, {})
        out.append(VeilleItem(
            key=key, label=label,
            realises=a.get(EntretienStatut.REALISE, 0),
            planifies=a.get(EntretienStatut.PLANIFIE, 0),
            en_retard=a.get(EntretienStatut.EN_RETARD, 0)))
    return out


# ------------------------------------------------------------------- Alertes
def alertes(db: Session) -> list[AlerteItem]:
    """Alertes RH DÉRIVÉES de signaux réels : hauts potentiels à suivre, entretiens
    en retard, souhaits de mobilité poussés (signal de rétention)."""
    out: list[AlerteItem] = []
    nb_hp = len(hauts_potentiels(db, limit=50))
    if nb_hp:
        out.append(AlerteItem(
            kind="potential", severity="info",
            titre=f"{nb_hp} haut(s) potentiel(s) identifié(s)",
            texte="Des collaborateurs au niveau de compétences élevé sont à suivre pour la succession.",
            cta="Voir les hauts potentiels", to_route="hautsPotentiels"))
    en_retard = _count(db, select(Entretien.id).where(Entretien.statut == EntretienStatut.EN_RETARD))
    if en_retard:
        out.append(AlerteItem(
            kind="succession", severity="warn",
            titre=f"{en_retard} entretien(s) en retard",
            texte="Des entretiens n'ont pas été menés dans les délais.",
            cta="Planifier", to_route="veille"))
    mobilites = _count(db, select(Souhait.id).where(Souhait.pushed.is_(True)))
    if mobilites:
        out.append(AlerteItem(
            kind="retention", severity="info",
            titre=f"{mobilites} souhait(s) de mobilité exprimé(s)",
            texte="Des collaborateurs ont poussé un souhait d'évolution — opportunité de rétention.",
            cta="Voir les souhaits", to_route="souhaitsRecus"))
    return out
