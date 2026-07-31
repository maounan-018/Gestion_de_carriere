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

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from app.models.profil import Profil, ProfilCompetence
from app.models.offre import Offre, OffreStatut, OffreCompetence
from app.models.candidature import Candidature
from app.models.souhait import Souhait
from app.models.user import User
from app.models.formation import Formation
from app.models.entretien import Entretien, EntretienType, EntretienStatut
from app.schemas.dashboard import (KpiItem, CartoMatrix, CartoLigne, FamilleCompetence,
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
# Famille par défaut quand la compétence détenue n'a pas de catégorie renseignée.
_FAM_DEFAUT = "transversale"


def _humanize(key: str) -> str:
    """Clé de département → libellé lisible ('retail_banking' → 'Retail Banking')."""
    return key.replace("_", " ").title()


def cartographie(db: Session) -> CartoMatrix:
    """Cartographie en MATRICE data-driven : pôles (lignes) × familles de compétences
    (colonnes = catégories présentes en base). Aucune taxonomie figée — tout pôle ou
    toute famille présent apparaît automatiquement (N × M variables)."""
    fam = func.coalesce(ProfilCompetence.categorie, _FAM_DEFAUT)

    # Colonnes : familles distinctes réellement présentes (triées).
    familles = [r[0] for r in db.execute(
        select(fam).join(Profil, Profil.id == ProfilCompetence.profil_id)
        .where(Profil.departement_key.isnot(None))
        .distinct().order_by(fam)).all()]

    # Effectif + niveau moyen global par pôle.
    effectifs = dict(db.execute(
        select(Profil.departement_key, func.count(Profil.id))
        .where(Profil.departement_key.isnot(None))
        .group_by(Profil.departement_key)).all())
    moy_globales = dict(db.execute(
        select(Profil.departement_key, func.avg(ProfilCompetence.niveau))
        .join(ProfilCompetence, ProfilCompetence.profil_id == Profil.id)
        .group_by(Profil.departement_key)).all())

    # Cellules : niveau moyen par (pôle, famille).
    cells: dict[tuple[str, str], float | None] = {}
    for dept, f, moy in db.execute(
            select(Profil.departement_key, fam, func.avg(ProfilCompetence.niveau))
            .join(ProfilCompetence, ProfilCompetence.profil_id == Profil.id)
            .group_by(Profil.departement_key, fam)).all():
        cells[(dept, f)] = round(moy, 2) if moy is not None else None

    # Noms des profils par pôle (aperçu pour le détail).
    people: dict[str, list[str]] = {}
    for dept, nom, prenom in db.execute(
            select(Profil.departement_key, Profil.nom, Profil.prenom)
            .where(Profil.departement_key.isnot(None))
            .order_by(Profil.nom)).all():
        people.setdefault(dept, []).append(f"{prenom or ''} {nom}".strip())

    # Lignes triées par effectif décroissant (pôles les plus fournis en tête).
    lignes: list[CartoLigne] = []
    for dept, eff in sorted(effectifs.items(), key=lambda kv: -kv[1]):
        moy = moy_globales.get(dept)
        lignes.append(CartoLigne(
            departement_key=dept, label=_humanize(dept), effectif=eff,
            niveau_moyen=round(moy, 2) if moy is not None else None,
            niveaux=[cells.get((dept, f)) for f in familles],
            people=people.get(dept, [])[:12]))
    return CartoMatrix(familles=familles, lignes=lignes)


# ------------------------------------------------- Familles de compétences
def _tension(demande: int, profils_couverts: int) -> str:
    """Signal INDICATIF de tension sur une famille : demande (offres ouvertes) vs
    couverture interne (profils la détenant). Pas de demande -> faible ; demandé mais
    personne ne le détient -> forte ; sinon selon le ratio couverts/demande."""
    if demande == 0:
        return "faible"
    if profils_couverts == 0:
        return "forte"
    ratio = profils_couverts / demande
    if ratio >= 2:
        return "faible"
    if ratio >= 1:
        return "moyenne"
    return "forte"


def familles(db: Session) -> list[FamilleCompetence]:
    """Cartographie par FAMILLE de compétences (catégorie), au-delà des départements :
    offre interne DÉTENUE (profils/compétences/niveau) confrontée à la DEMANDE des
    offres ouvertes → signal de tension. Familles = catégories réellement présentes
    (défaut `transversale` quand la compétence n'est pas catégorisée)."""
    fam_p = func.coalesce(ProfilCompetence.categorie, _FAM_DEFAUT)
    supply = {
        f: (det, couv, moy)
        for f, det, couv, moy in db.execute(
            select(fam_p, func.count(ProfilCompetence.id),
                   func.count(distinct(ProfilCompetence.profil_id)),
                   func.avg(ProfilCompetence.niveau))
            .group_by(fam_p)).all()
    }
    fam_o = func.coalesce(OffreCompetence.categorie, _FAM_DEFAUT)
    demand = dict(db.execute(
        select(fam_o, func.count(OffreCompetence.id))
        .join(Offre, Offre.id == OffreCompetence.offre_id)
        .where(Offre.statut == OffreStatut.OUVERTE)
        .group_by(fam_o)).all())

    out: list[FamilleCompetence] = []
    for f in sorted(set(supply) | set(demand)):
        det, couv, moy = supply.get(f, (0, 0, None))
        dem = demand.get(f, 0)
        out.append(FamilleCompetence(
            famille=f, detenues=det, profils_couverts=couv,
            niveau_moyen=round(moy, 2) if moy is not None else None,
            demande=dem, tension=_tension(dem, couv)))
    return out


# ------------------------------------------------------------- Synthèse RH
def synthese(db: Session) -> dict:
    """Vue consolidée pour étoffer le tableau de bord RH : effectif total,
    répartition par pôle, pipeline des candidatures par statut, et nombre de
    familles de compétences en tension FORTE (signal de priorité)."""
    effectif = _count(db, select(Profil.id))
    par_pole = [
        {"pole": _humanize(k) if k else "—", "effectif": n}
        for k, n in db.execute(
            select(Profil.departement_key, func.count(Profil.id))
            .group_by(Profil.departement_key)
            .order_by(func.count(Profil.id).desc())).all()
    ]
    candidatures_par_statut = [
        {"statut": s, "nombre": n}
        for s, n in db.execute(
            select(Candidature.statut, func.count(Candidature.id))
            .group_by(Candidature.statut)
            .order_by(func.count(Candidature.id).desc())).all()
    ]
    familles_en_tension = sum(1 for f in familles(db) if f.tension == "forte")
    return {
        "effectif": effectif,
        "par_pole": par_pole,
        "candidatures_par_statut": candidatures_par_statut,
        "familles_en_tension": familles_en_tension,
    }


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
