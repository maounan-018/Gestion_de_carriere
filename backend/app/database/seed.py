#!/usr/bin/env python3
"""
database/seed.py — Seed des comptes de démo + personas synthétiques (Bloc C).

RÔLE
    Provisionne les comptes nécessaires pour tester l'authentification et le RBAC
    route par route, et les personas des maquettes (Marc Bennani / Jean-Marc Dupont
    / Nadia Alami) avec leur `Profil` de carrière. Sans ces comptes, `users=0` et
    aucun guard RBAC n'est éprouvable.

    Deux leviers, alignés sur la config :
      - SEED_DEMO_ACCOUNTS      -> crée les COMPTES (admin + 3 personas) pour l'auth/RBAC ;
      - SEED_SYNTHETIC_PERSONAS -> crée les PROFILS de carrière liés (données métier).

IDEMPOTENT
    Ré-exécutable sans doublon : chaque entité est repérée par une clé naturelle
    (email pour les users, matricule/user_id pour les profils) et ignorée si présente.

SÉCURITÉ / ÉTIQUETAGE
    - Tout est marqué SYNTHÉTIQUE : User.type = "synthetic", Profil.synthetique = True.
      (⚠️ jamais en production — cf. règle « toujours étiqueter les données fabriquées ».)
    - Mots de passe hachés PBKDF2 (core.security). Mot de passe de démo COMMUN, lu depuis
      SEED_DEMO_PASSWORD (défaut ci-dessous) — usage démo/local UNIQUEMENT.
    - Chaque création de compte émet un évènement d'audit USER_CREATED.

USAGE
    conda run -n bmci-carrieres python -m app.database.seed
    (piloter la base via la variable d'env DATABASE_PATH pour cibler une copie.)

EMPLACEMENT MVC
    Couche "database" : amorçage de données.
"""

from __future__ import annotations

import os
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User, Role, UserType
from app.models.profil import Profil, ProfilCompetence, CompetenceSource
from app.models.fiche import Fiche, FicheCompetence
from app.models.offre import Offre
from app.models.candidature import Candidature
from app.models.notification import Notification
from app.models.souhait import Souhait, SouhaitStatut
from app.models.formation import Formation
from app.models.carriere import ProfilStation, PeerReview, StationEtat
from app.models.entretien import Entretien, EntretienType, EntretienStatut
from app.models.audit_log import AuditEventType
from app.schemas.offre import OffreCreate
from app.schemas.candidature import CandidatureCreate
from app.services import audit_service, offre_service, candidature_service

logger = logging.getLogger(__name__)

# Mot de passe de démo COMMUN (local/démo uniquement). Surchargable par env.
DEFAULT_DEMO_PASSWORD = "REDACTED-SEE-ENV-LOCAL"

# --- Définition des comptes/personas de démo ---------------------------------
# email volontairement en .local (jamais une vraie adresse) ; matricules fictifs.
ADMIN = {
    "email": "admin@bmci.local", "name": "Administrateur (démo)",
    "role": Role.ADMIN, "matricule": "ADM-001", "departement_key": None,
}

# Ordre : managers/RH avant le collaborateur (résolution du manager_id par email).
PERSONAS = [
    {
        "email": "nadia.alami@bmci.local", "name": "Nadia Alami", "role": Role.RH,
        "departement_key": "ressources_humaines", "matricule": "RH-2043",
        "poste_actuel": "Responsable RH", "manager_email": None,
        "aspirations": "Piloter la cartographie des compétences du Groupe.",
        "competences": [
            ("Gestion des talents", 4), ("Droit du travail", 4),
            ("Conduite d'entretien", 5), ("Analyse de données RH", 3),
        ],
        "competences_from_fiche": None,
    },
    {
        "email": "jeanmarc.dupont@bmci.local", "name": "Jean-Marc Dupont", "role": Role.MANAGER,
        "departement_key": "retail_banking", "matricule": "MG-1088",
        "poste_actuel": "Directeur d'agence", "manager_email": None,
        "aspirations": "Évoluer vers un poste de Directeur Exécutif du réseau.",
        "competences": [
            ("Management d'équipe", 5), ("Développement commercial", 4),
            ("Gestion du risque de crédit", 3), ("Relation client grands comptes", 4),
        ],
        "competences_from_fiche": None,
    },
    {
        "email": "marc.bennani@bmci.local", "name": "Marc Bennani", "role": Role.COLLAB,
        "departement_key": "retail_banking", "matricule": "CB-3390",
        "poste_actuel": "Conseiller clientèle particuliers", "manager_email": "jeanmarc.dupont@bmci.local",
        "aspirations": "Devenir Chargé d'affaires professionnels.",
        # Compétences dérivées de la vraie fiche #1 (matching réaliste, partiel).
        "competences": [],
        "competences_from_fiche": 1,
    },
]


def _get_or_create_user(db: Session, spec: dict, password: str) -> tuple[User, bool]:
    """Repère par email (lowercase). Crée si absent. Renvoie (user, created)."""
    email = spec["email"].strip().lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing, False
    user = User(
        email=email, name=spec["name"], role=spec["role"], type=UserType.SYNTHETIC,
        password_hash=hash_password(password), is_active=True,
        departement_key=spec.get("departement_key"), matricule=spec.get("matricule"),
    )
    db.add(user)
    db.flush()  # -> user.id
    return user, True


def _fiche_competence_libelles(db: Session, fiche_id: int, limit: int = 6) -> list[str]:
    return list(db.scalars(
        select(FicheCompetence.libelle).where(FicheCompetence.fiche_id == fiche_id)
        .order_by(FicheCompetence.id).limit(limit)
    ).all())


def _get_or_create_profil(db: Session, user: User, spec: dict) -> tuple[Profil | None, bool]:
    """Crée le Profil de carrière lié au user (repéré par user_id). (profil, created)."""
    existing = db.scalar(select(Profil).where(Profil.user_id == user.id))
    if existing:
        return existing, False
    # name = "Prénom Nom" -> prénom = 1er mot, nom = le reste (tolère un seul mot).
    prenom_val, nom_val = (spec["name"].split(" ", 1) + [""])[:2]
    p = Profil(
        user_id=user.id, nom=nom_val or spec["name"], prenom=prenom_val,
        matricule=spec.get("matricule"), poste_actuel=spec.get("poste_actuel"),
        departement_key=spec.get("departement_key"), aspirations=spec.get("aspirations"),
        synthetique=True,
    )
    db.add(p)
    db.flush()  # -> p.id

    # Compétences : explicites (libellé, niveau) et/ou dérivées d'une fiche réelle.
    comps: list[tuple[str, int | None]] = list(spec.get("competences") or [])
    if spec.get("competences_from_fiche"):
        niveaux = [4, 3, 5, 3, 4, 2]
        for i, lib in enumerate(_fiche_competence_libelles(db, spec["competences_from_fiche"])):
            comps.append((lib, niveaux[i % len(niveaux)]))
    for libelle, niveau in comps:
        db.add(ProfilCompetence(
            profil_id=p.id, libelle=libelle, niveau=niveau,
            source=CompetenceSource.DECLARATIF,
        ))
    return p, True


# --- Offres + candidatures synthétiques (débloque les écrans offres/revue) ----
# Plan appliqué aux fiches choisies (une offre par fiche) : (type, statut, créateur, manager ?).
# Les 2 premières (offre_poste ouvertes, poussées RH) servent de cibles de « revue candidats ».
_OFFRE_PLAN = [
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),  # cible revue #1
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),  # cible revue #2
    ("mission",     "ouverte",   "jeanmarc.dupont@bmci.local", True),   # cible Marc (#2)
    ("gig",         "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("projet",      "brouillon", "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "pourvue",   "nadia.alami@bmci.local",     False),
    # --- Catalogue élargi : postes/missions/projets répartis sur les départements ---
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("mission",     "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("projet",      "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("mission",     "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("gig",         "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("mission",     "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("projet",      "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("mission",     "ouverte",   "jeanmarc.dupont@bmci.local", True),
    ("offre_poste", "ouverte",   "nadia.alami@bmci.local",     False),
    ("gig",         "ouverte",   "jeanmarc.dupont@bmci.local", True),
]
_TYPE_LABEL = {"mission": "Mission", "projet": "Projet", "gig": "Gig"}  # offre_poste = pas de suffixe

# Candidats synthétiques : (nom, matricule, index de la fiche cible (0|1), nb de
# compétences reprises de cette fiche). Moins de compétences = score plus bas → étalement.
_CANDIDATS = [
    ("Salma Idrissi",   "DEMO-C1", 0, 6),
    ("Youssef Alaoui",  "DEMO-C2", 0, 4),
    ("Hicham Berrada",  "DEMO-C3", 0, 2),
    ("Imane Cherkaoui", "DEMO-C4", 1, 5),
    ("Karim Sabri",     "DEMO-C5", 1, 3),
]
_NIVEAUX = [4, 3, 5, 3, 4, 2, 4, 3]  # niveaux tournants (1-5) pour varier les profils


def _fiche_competences_rows(db: Session, fiche_id: int, limit: int = 8) -> list[FicheCompetence]:
    return list(db.scalars(
        select(FicheCompetence).where(FicheCompetence.fiche_id == fiche_id)
        .order_by(FicheCompetence.id).limit(limit)
    ).all())


def _pick_offre_fiches(db: Session, n: int) -> list[Fiche]:
    """Choisit `n` fiches (les + petits ids ayant ≥3 compétences) — déterministe,
    et garantit des attendus non vides pour que le score d'une candidature ait du sens."""
    ids = db.scalars(
        select(FicheCompetence.fiche_id).group_by(FicheCompetence.fiche_id)
        .having(func.count() >= 3).order_by(FicheCompetence.fiche_id).limit(n)
    ).all()
    return [f for f in (db.get(Fiche, i) for i in ids) if f is not None]


def _seed_offres(db: Session, fiches: list[Fiche],
                 users_by_email: dict[str, User]) -> tuple[list[int], dict]:
    """Crée une offre par fiche selon _OFFRE_PLAN (idempotent par titre+fiche).
    Renvoie (offre_ids alignés sur `fiches`, résumé créées/existantes)."""
    res = {"offres_created": [], "offres_existing": []}
    offre_ids: list[int] = []
    mgr = users_by_email.get("jeanmarc.dupont@bmci.local")
    for i, fiche in enumerate(fiches):
        type_, statut, creator_email, avec_mgr = _OFFRE_PLAN[i % len(_OFFRE_PLAN)]
        suffix = _TYPE_LABEL.get(type_)
        titre = f"{fiche.intitule_poste} · {suffix}" if suffix else fiche.intitule_poste
        existing = db.scalar(select(Offre).where(Offre.titre == titre, Offre.fiche_id == fiche.id))
        if existing:
            offre_ids.append(existing.id)
            res["offres_existing"].append(titre)
            continue
        creator = users_by_email.get(creator_email)
        out = offre_service.create_offre(db, OffreCreate(
            titre=titre, fiche_id=fiche.id, type=type_, statut=statut,
            departement_key=fiche.departement_key, perimetre_bmci=fiche.perimetre_bmci,
            created_by=creator.id if creator else None,
            manager_id=mgr.id if (avec_mgr and mgr) else None,
            synthetique=True,
        ))
        offre_ids.append(out.id)
        res["offres_created"].append(titre)
    return offre_ids, res


def _seed_candidate_profils(db: Session, fiches: list[Fiche],
                            manager_id: int | None = None) -> tuple[list[tuple[Profil, int]], dict]:
    """Crée les profils candidats synthétiques (sans compte), compétences reprises
    partiellement de leur fiche cible. Rattachés au manager `manager_id` (alimente
    l'écran « équipe »). Idempotent par matricule. Renvoie
    ([(profil, index_fiche_cible)], résumé)."""
    res = {"candidats_created": [], "candidats_existing": []}
    out: list[tuple[Profil, int]] = []
    for nom_complet, matricule, cible_idx, nb in _CANDIDATS:
        if cible_idx >= len(fiches):
            continue
        fiche = fiches[cible_idx]
        existing = db.scalar(select(Profil).where(Profil.matricule == matricule))
        if existing:
            if manager_id and existing.manager_id is None:
                existing.manager_id = manager_id  # backfill du lien manager
            out.append((existing, cible_idx))
            res["candidats_existing"].append(nom_complet)
            continue
        prenom_val, nom_val = (nom_complet.split(" ", 1) + [""])[:2]
        p = Profil(
            user_id=None, nom=nom_val or nom_complet, prenom=prenom_val, matricule=matricule,
            poste_actuel=fiche.intitule_poste, departement_key=fiche.departement_key,
            manager_id=manager_id,
            synthetique=True,  # ⚠️ candidat de démonstration (donnée fabriquée)
        )
        db.add(p)
        db.flush()  # -> p.id
        for j, fc in enumerate(_fiche_competences_rows(db, fiche.id, limit=nb)):
            db.add(ProfilCompetence(
                profil_id=p.id, libelle=fc.libelle, categorie=fc.categorie,
                skill_id=fc.skill_id, skill_label_fr=fc.skill_label_fr,
                niveau=_NIVEAUX[j % len(_NIVEAUX)], source=CompetenceSource.DECLARATIF,
            ))
        out.append((p, cible_idx))
        res["candidats_created"].append(nom_complet)
    db.commit()
    return out, res


def _seed_candidatures(db: Session, offre_ids: list[int],
                       candidate_profils: list[tuple[Profil, int]],
                       marc_profil: Profil | None) -> dict:
    """Dépose les candidatures (score calculé par le service). Idempotent (unicité
    profil/offre pré-vérifiée). Cibles : offres ouvertes #0/#1 + mission (#2)."""
    res = {"candidatures_created": 0, "candidatures_existing": 0}

    def _postuler(offre_id: int | None, profil_id: int | None, motivation: str) -> None:
        if offre_id is None or profil_id is None:
            return
        if db.scalar(select(Candidature).where(
                Candidature.offre_id == offre_id, Candidature.profil_id == profil_id)):
            res["candidatures_existing"] += 1
            return
        candidature_service.create_candidature(db, CandidatureCreate(
            offre_id=offre_id, profil_id=profil_id, motivation=motivation))
        res["candidatures_created"] += 1

    def _offre(idx: int) -> int | None:
        return offre_ids[idx] if idx < len(offre_ids) else None

    # Chaque candidat -> l'offre de sa fiche cible (revue candidats #0/#1).
    for profil, cible_idx in candidate_profils:
        _postuler(_offre(cible_idx), profil.id, "[DÉMO] Candidature synthétique")

    # Le collaborateur Marc Bennani -> cible #0 (poste) + la mission (#2).
    if marc_profil is not None:
        _postuler(_offre(0), marc_profil.id, "[DÉMO] Intéressé par cette évolution.")
        _postuler(_offre(2), marc_profil.id, "[DÉMO] Disponible pour cette mission.")
    return res


# --- Catalogue de formations synthétiques (à la place du LMS) -----------------
_FORMATIONS = [
    {"titre": "Bâle III & gestion des risques bancaires", "provider": "BMCI Academy",
     "duree": "16 h", "niveau": "Intermédiaire", "domaine": "Risque & Conformité",
     "tags": "risque,bâle,crédit", "skill_cible": "Gestion du risque de crédit"},
    {"titre": "IFRS 9 en pratique", "provider": "BMCI Academy", "duree": "12 h",
     "niveau": "Avancé", "domaine": "Finance", "tags": "ifrs,comptabilité,finance",
     "skill_cible": "Analyse financière"},
    {"titre": "Analyse de données RH avec Excel", "provider": "OpenClassrooms",
     "duree": "8 h", "niveau": "Débutant", "domaine": "Data", "tags": "excel,rh,données",
     "skill_cible": "Analyse de données RH"},
    {"titre": "Management d'équipe : les fondamentaux", "provider": "CrossKnowledge",
     "duree": "10 h", "niveau": "Débutant", "domaine": "Management", "tags": "management,leadership",
     "skill_cible": "Management d'équipe"},
    {"titre": "Conduite de l'entretien annuel", "provider": "BMCI Academy", "duree": "6 h",
     "niveau": "Intermédiaire", "domaine": "Management", "tags": "entretien,rh,management",
     "skill_cible": "Conduite d'entretien"},
    {"titre": "Relation client grands comptes", "provider": "Cegos", "duree": "14 h",
     "niveau": "Intermédiaire", "domaine": "Commercial", "tags": "commercial,client,corporate",
     "skill_cible": "Relation client grands comptes"},
    {"titre": "Cybersécurité pour les métiers bancaires", "provider": "OpenClassrooms",
     "duree": "12 h", "niveau": "Intermédiaire", "domaine": "IT & Digital", "tags": "cyber,sécurité,it",
     "skill_cible": "Cybersécurité"},
    {"titre": "Lutte anti-blanchiment (LCB-FT)", "provider": "BMCI Academy", "duree": "8 h",
     "niveau": "Intermédiaire", "domaine": "Risque & Conformité", "tags": "conformité,lcb-ft,réglementaire",
     "skill_cible": "Conformité réglementaire"},
    {"titre": "Financement des professionnels", "provider": "Cegos", "duree": "10 h",
     "niveau": "Avancé", "domaine": "Commercial", "tags": "commercial,crédit,pro",
     "skill_cible": "Développement commercial"},
    {"titre": "Leadership et conduite du changement", "provider": "CrossKnowledge",
     "duree": "12 h", "niveau": "Avancé", "domaine": "Management", "tags": "leadership,changement",
     "skill_cible": "Leadership"},
    {"titre": "Trade Finance et opérations internationales", "provider": "BMCI Academy",
     "duree": "14 h", "niveau": "Avancé", "domaine": "Commercial", "tags": "trade,international,credoc",
     "skill_cible": "Trade finance"},
    {"titre": "Gestion actif-passif (ALM) et trésorerie", "provider": "Cegos",
     "duree": "16 h", "niveau": "Avancé", "domaine": "Finance", "tags": "alm,trésorerie,liquidité",
     "skill_cible": "Gestion ALM"},
    {"titre": "Banque participative : principes et produits", "provider": "BMCI Academy",
     "duree": "10 h", "niveau": "Intermédiaire", "domaine": "Commercial", "tags": "participative,mourabaha,ijara",
     "skill_cible": "Banque participative"},
    {"titre": "Data science appliquée à la banque", "provider": "OpenClassrooms",
     "duree": "24 h", "niveau": "Avancé", "domaine": "Data", "tags": "python,machine learning,data",
     "skill_cible": "Data science"},
    {"titre": "Power BI : tableaux de bord décisionnels", "provider": "OpenClassrooms",
     "duree": "10 h", "niveau": "Intermédiaire", "domaine": "Data", "tags": "power bi,dataviz,reporting",
     "skill_cible": "Business intelligence"},
    {"titre": "Méthodes agiles : Scrum et Kanban", "provider": "CrossKnowledge",
     "duree": "8 h", "niveau": "Débutant", "domaine": "IT & Digital", "tags": "agile,scrum,projet",
     "skill_cible": "Gestion de projet agile"},
    {"titre": "RGPD et protection des données personnelles", "provider": "Cegos",
     "duree": "6 h", "niveau": "Intermédiaire", "domaine": "Risque & Conformité", "tags": "rgpd,dpo,données",
     "skill_cible": "Protection des données"},
    {"titre": "Audit interne et contrôle permanent", "provider": "BMCI Academy",
     "duree": "12 h", "niveau": "Avancé", "domaine": "Risque & Conformité", "tags": "audit,contrôle,risque",
     "skill_cible": "Contrôle interne"},
    {"titre": "Négociation commerciale avancée", "provider": "Cegos",
     "duree": "10 h", "niveau": "Intermédiaire", "domaine": "Commercial", "tags": "négociation,vente,client",
     "skill_cible": "Négociation"},
    {"titre": "Prise de parole et communication d'impact", "provider": "CrossKnowledge",
     "duree": "8 h", "niveau": "Débutant", "domaine": "Développement personnel", "tags": "communication,oral,posture",
     "skill_cible": "Communication"},
    {"titre": "Gestion du stress et efficacité personnelle", "provider": "CrossKnowledge",
     "duree": "6 h", "niveau": "Débutant", "domaine": "Développement personnel", "tags": "bien-être,organisation,stress",
     "skill_cible": "Efficacité personnelle"},
    {"titre": "Anglais professionnel pour la banque", "provider": "OpenClassrooms",
     "duree": "20 h", "niveau": "Intermédiaire", "domaine": "Langues", "tags": "anglais,langue,professionnel",
     "skill_cible": "Anglais professionnel"},
    {"titre": "Excel avancé : modélisation financière", "provider": "OpenClassrooms",
     "duree": "12 h", "niveau": "Avancé", "domaine": "Finance", "tags": "excel,modélisation,finance",
     "skill_cible": "Modélisation financière"},
    {"titre": "Monétique et moyens de paiement", "provider": "BMCI Academy",
     "duree": "10 h", "niveau": "Intermédiaire", "domaine": "IT & Digital", "tags": "monétique,cartes,paiement",
     "skill_cible": "Monétique"},
]


def _seed_formations(db: Session) -> list[str]:
    """Catalogue de formations synthétiques (idempotent par titre)."""
    created: list[str] = []
    for f in _FORMATIONS:
        if db.scalar(select(Formation).where(Formation.titre == f["titre"])):
            continue
        db.add(Formation(**f, synthetique=True))
        created.append(f["titre"])
    db.commit()
    return created


# --- Notifications synthétiques par persona -----------------------------------
# email -> [(type, titre, texte, route_destination)]
_NOTIFS = {
    "marc.bennani@bmci.local": [
        ("offre", "Nouvelle offre compatible",
         "Une offre « Conseiller clientèle » correspond à 78 % à votre profil.", "offres"),
        ("souhait", "Votre manager a consulté vos souhaits",
         "Jean-Marc Dupont a consulté vos souhaits d'évolution.", "souhaitSuivi"),
        ("entretien", "Entretien annuel à préparer",
         "Pensez à préparer votre entretien de carrière.", "entretien"),
    ],
    "jeanmarc.dupont@bmci.local": [
        ("souhait", "Nouveau souhait d'un collaborateur",
         "Marc Bennani a poussé un souhait d'évolution.", "souhaitsRecus"),
        ("entretien", "Entretiens d'équipe à mener",
         "Il vous reste des entretiens annuels à réaliser ce trimestre.", "entretien"),
    ],
    "nadia.alami@bmci.local": [
        ("action", "Offre en validation",
         "Une offre attend votre validation finale.", "rhOffres"),
        ("info", "Cartographie mise à jour",
         "La cartographie des compétences a été rafraîchie.", "cartographie"),
    ],
}


def _seed_notifications(db: Session, users_by_email: dict[str, User]) -> int:
    """Notifications de démo par persona (idempotent par destinataire+titre)."""
    created = 0
    for email, items in _NOTIFS.items():
        u = users_by_email.get(email)
        if not u:
            continue
        for type_, titre, texte, to_route in items:
            if db.scalar(select(Notification).where(
                    Notification.user_id == u.id, Notification.titre == titre)):
                continue
            db.add(Notification(user_id=u.id, type=type_, titre=titre, texte=texte, to_route=to_route))
            created += 1
    db.commit()
    return created


# --- Souhaits d'évolution du collaborateur Marc (dont un poussé au manager) ----
_SOUHAITS_MARC = [
    ("Évoluer vers Chargé d'affaires professionnels", "carriere", "1-2 ans",
     "Je souhaite évoluer vers un poste de chargé d'affaires professionnels.", True),
    ("Participer à une mission transverse ESG", "mission", "6 mois",
     "Intéressé par une mission ponctuelle sur le reporting ESG.", False),
]


def _seed_souhaits(db: Session, marc_profil: Profil | None) -> int:
    """Souhaits de démo pour Marc (idempotent par profil+titre). Le souhait poussé
    devient visible du manager via /api/souhaits/recus."""
    if marc_profil is None:
        return 0
    created = 0
    for titre, kind, horizon, desc, pushed in _SOUHAITS_MARC:
        if db.scalar(select(Souhait).where(
                Souhait.profil_id == marc_profil.id, Souhait.titre == titre)):
            continue
        db.add(Souhait(
            profil_id=marc_profil.id, titre=titre, kind=kind, horizon=horizon,
            description=desc, pushed=pushed,
            statut=SouhaitStatut.POUSSE if pushed else SouhaitStatut.BROUILLON,
        ))
        created += 1
    db.commit()
    return created


# --- Carrière enrichie des personas (stations + avis des pairs) ---------------
# email -> (stations [(periode, titre, desc, etat, ordre)], avis [(auteur, role, initiales, texte, etoiles)])
_P, _A, _O = StationEtat.PASSE, StationEtat.ACTUEL, StationEtat.OBJECTIF
_CARRIERE = {
    "marc.bennani@bmci.local": (
        [("2017", "Téléconseiller banque à distance", "Entrée à la BMCI, centre de relation client.", _P, 0),
         ("2020", "Conseiller clientèle digitale", "Accompagnement des clients sur les canaux en ligne.", _P, 1),
         ("Aujourd'hui", "Conseiller clientèle particuliers", "Poste actuel — portefeuille de clients particuliers.", _A, 2),
         ("Objectif", "Chargé d'affaires professionnels", "Évolution visée (1-2 ans).", _O, 3)],
        [("Jean-Marc Dupont", "Directeur d'agence", "JD",
          "Très fiable, excellent relationnel client. Prêt pour plus de responsabilités.", 5),
         ("Salma Idrissi", "Collègue", "SI",
          "Toujours prêt à aider l'équipe, rigoureux sur la conformité.", 4)],
    ),
    "jeanmarc.dupont@bmci.local": (
        [("2016", "Conseiller professionnels", "Portefeuille PME.", _P, 0),
         ("2020", "Directeur adjoint", "Pilotage d'équipe commerciale.", _P, 1),
         ("Aujourd'hui", "Directeur d'agence", "Poste actuel.", _A, 2),
         ("Objectif", "Directeur Exécutif du réseau", "Trajectoire dirigeant.", _O, 3)],
        [("Nadia Alami", "Responsable RH", "NA",
          "Manager engagé, développe très bien ses collaborateurs.", 5)],
    ),
    "nadia.alami@bmci.local": (
        [("2018", "Chargée RH", "Gestion des carrières du pôle.", _P, 0),
         ("Aujourd'hui", "Responsable RH", "Poste actuel.", _A, 1),
         ("Objectif", "Directrice des Talents", "Cartographie Groupe.", _O, 2)],
        [("Direction Générale", "Comité de direction", "DG",
          "Vision stratégique des talents, moteur de la transformation RH.", 5)],
    ),
}


def _seed_carriere(db: Session, users_by_email: dict[str, User]) -> int:
    """Stations de progression + avis des pairs pour les personas. Idempotent :
    on ne (re)sème stations/avis d'un profil que s'il n'en a pas encore."""
    n = 0
    for email, (stations, avis) in _CARRIERE.items():
        u = users_by_email.get(email)
        if not u:
            continue
        p = db.scalar(select(Profil).where(Profil.user_id == u.id))
        if not p:
            continue
        if not db.scalar(select(ProfilStation.id).where(ProfilStation.profil_id == p.id)):
            for periode, titre, desc, etat, ordre in stations:
                db.add(ProfilStation(profil_id=p.id, periode=periode, titre=titre,
                                     description=desc, etat=etat, ordre=ordre))
                n += 1
        if not db.scalar(select(PeerReview.id).where(PeerReview.profil_id == p.id)):
            for auteur, role, ini, texte, etoiles in avis:
                db.add(PeerReview(profil_id=p.id, auteur_nom=auteur, auteur_role=role,
                                  initiales=ini, texte=texte, etoiles=etoiles))
                n += 1
    db.commit()
    return n


# --- Entretiens (veille RH : réalisés / planifiés / en retard) ----------------
_STATUTS_CYCLE = [EntretienStatut.REALISE, EntretienStatut.PLANIFIE, EntretienStatut.EN_RETARD]


def _seed_entretiens(db: Session) -> int:
    """Un entretien annuel + un entretien RH par profil, statut en rotation
    (réalisé/planifié/en retard) pour peupler la veille. Idempotent par profil."""
    profils = db.scalars(select(Profil).order_by(Profil.id)).all()
    created = 0
    for i, p in enumerate(profils):
        if db.scalar(select(Entretien.id).where(Entretien.profil_id == p.id)):
            continue
        for j, type_ in enumerate((EntretienType.ANNUEL, EntretienType.RH)):
            db.add(Entretien(profil_id=p.id, type=type_,
                             statut=_STATUTS_CYCLE[(i + j) % len(_STATUTS_CYCLE)]))
            created += 1
    db.commit()
    return created


# --- Cartographie : profils synthétiques répartis sur TOUTE l'organisation réelle ---
# Source = référentiel config/departements_metiers.yaml (6 pôles macro, ~34 départements,
# ~165 métiers). Peuple la heatmap RH (départements × 6 familles de compétences) de façon
# riche, variée et FIDÈLE à l'organigramme BMCI, au lieu de quelques pôles inventés.
# ⚠️ Profils SYNTHÉTIQUES (synthetique=True, matricule `DEMO-CARTO-*`) — données de démo.

# Familles de compétences = colonnes de la heatmap (alignées sur le front `humanizeFamille`).
_CARTO_FAMILLES = ["metier", "comportementale", "transversale",
                   "outil_technologie", "leadership", "data"]

# Niveau de base (1-5) par (pôle macro → famille) : profil de compétences typique du pôle.
# Chaque département hérite du profil de son pôle, ± un léger jitter déterministe.
_POLE_PROFILE: dict[str, dict[str, int]] = {
    "Lignes métiers commerciales": {
        "metier": 4, "comportementale": 4, "transversale": 3,
        "outil_technologie": 3, "leadership": 3, "data": 3},
    "Marchés, international & filiales": {
        "metier": 4, "comportementale": 3, "transversale": 4,
        "outil_technologie": 3, "leadership": 3, "data": 4},
    "Risques, conformité & contrôle": {
        "metier": 4, "comportementale": 4, "transversale": 4,
        "outil_technologie": 3, "leadership": 3, "data": 3},
    "Finance, stratégie & pilotage": {
        "metier": 4, "comportementale": 3, "transversale": 4,
        "outil_technologie": 3, "leadership": 3, "data": 4},
    "Data, IT & digital": {
        "metier": 4, "comportementale": 3, "transversale": 3,
        "outil_technologie": 5, "leadership": 3, "data": 4},
    "Fonctions support & corporate": {
        "metier": 3, "comportementale": 4, "transversale": 4,
        "outil_technologie": 3, "leadership": 3, "data": 3},
}
_POLE_DEFAUT = {f: 3 for f in _CARTO_FAMILLES}

# Libellés représentatifs par famille (la famille "metier" reprend le métier réel du poste).
_FAM_LIBELLES: dict[str, list[str]] = {
    "comportementale": ["Rigueur", "Esprit d'analyse", "Sens du client",
                        "Adaptabilité", "Communication", "Esprit d'équipe"],
    "transversale": ["Gestion de projet", "Reporting réglementaire", "Veille réglementaire",
                     "Anglais professionnel", "Optimisation des process", "Conduite du changement"],
    "outil_technologie": ["Excel avancé", "SQL", "Python", "Outils SI métiers",
                          "Power BI", "Automatisation"],
    "leadership": ["Management d'équipe", "Pilotage d'activité", "Leadership collaboratif",
                   "Animation transverse"],
    "data": ["Analyse de données", "Business intelligence", "Modélisation",
             "Data quality", "Datavisualisation"],
}

_CARTO_PRENOMS = ["Youssef", "Fatima", "Rachid", "Sophia", "Omar", "Leïla", "Yassine",
                  "Nadia", "Karim", "Salma", "Mehdi", "Imane", "Hamza", "Sara",
                  "Anas", "Khadija", "Reda", "Meryem"]
_CARTO_NOMS = ["Alaoui", "Bennani", "Chraibi", "Idrissi", "Fassi", "Sekkat", "Tahiri",
               "Ouali", "Amrani", "Benjelloun", "El Malki", "Berrada", "Kabbaj",
               "Lahlou", "Naciri", "Squalli", "Tazi", "Zniber"]


def _carto_hash(s: str) -> int:
    """Hash déterministe (indépendant du PYTHONHASHSEED) pour varier profils/niveaux."""
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


def _seed_carto(db: Session) -> int:
    """Profils synthétiques répartis sur TOUS les départements réels (référentiel
    d'organisation), compétences taguées par famille → cartographie (heatmap) pleine,
    variée et fidèle à l'organigramme BMCI. Idempotent par matricule."""
    from app.services import cartography_service  # référentiel pôles/départements (YAML)

    try:
        depts = cartography_service.departements()
    except FileNotFoundError:
        depts = []

    created = 0
    for dept in depts:
        key = dept.get("key")
        if not key:
            continue
        pole = dept.get("pole") or ""
        metiers = dept.get("metiers") or [dept.get("nom", key)]
        base = _POLE_PROFILE.get(pole, _POLE_DEFAUT)
        n_profils = 1 + _carto_hash(key) % 3  # 1 à 3 profils/département → effectifs variés
        for n in range(n_profils):
            matricule = f"DEMO-CARTO-{key}-{n + 1}"
            if db.scalar(select(Profil).where(Profil.matricule == matricule)):
                continue
            h = _carto_hash(f"{key}-{n}")
            prenom = _CARTO_PRENOMS[h % len(_CARTO_PRENOMS)]
            nom = _CARTO_NOMS[(h // 7) % len(_CARTO_NOMS)]
            poste = metiers[h % len(metiers)]
            p = Profil(user_id=None, nom=nom, prenom=prenom, matricule=matricule,
                       poste_actuel=poste, departement_key=key, synthetique=True)
            db.add(p)
            db.flush()
            for fam in _CARTO_FAMILLES:
                jitter = (_carto_hash(f"{key}-{fam}-{n}") % 3) - 1  # -1, 0 ou +1
                niveau = max(1, min(5, base.get(fam, 3) + jitter))
                libelle = poste if fam == "metier" else \
                    _FAM_LIBELLES[fam][_carto_hash(f"{key}-{fam}") % len(_FAM_LIBELLES[fam])]
                db.add(ProfilCompetence(profil_id=p.id, libelle=libelle, categorie=fam,
                                        niveau=niveau, source=CompetenceSource.DECLARATIF))
            created += 1
    db.commit()
    return created


def seed_all(db: Session, *, demo_accounts: bool, synthetic_personas: bool,
             password: str, synthetic_offers: bool = True) -> dict:
    """Amorce comptes + profils + offres/candidatures selon les leviers.
    Idempotent. Renvoie un résumé. `synthetic_offers` no-op sans fiches en base
    (défaut True → rétro-compatible avec les appelants existants)."""
    summary = {"users_created": [], "users_existing": [], "profils_created": [], "profils_existing": [],
               "offres_created": [], "offres_existing": [],
               "candidats_created": [], "candidats_existing": [],
               "candidatures_created": 0, "candidatures_existing": 0,
               "formations_created": [], "notifications_created": 0, "souhaits_created": 0,
               "carriere_created": 0, "entretiens_created": 0, "carto_created": 0}

    if not demo_accounts:
        logger.info("SEED_DEMO_ACCOUNTS=false — aucun compte créé.")
        return summary

    specs = [ADMIN] + PERSONAS
    users_by_email: dict[str, User] = {}
    audit_pending: list[tuple[int, str, str]] = []  # (id, email, role) à tracer APRÈS commit

    # 1) Comptes
    for spec in specs:
        user, created = _get_or_create_user(db, spec, password)
        users_by_email[spec["email"].strip().lower()] = user
        (summary["users_created"] if created else summary["users_existing"]).append(user.email)
        if created:
            audit_pending.append((user.id, user.email, user.role))

    # 2) Liens hiérarchiques (manager_id) une fois tous les users présents
    for spec in PERSONAS:
        mgr_email = spec.get("manager_email")
        if mgr_email:
            u = users_by_email[spec["email"].strip().lower()]
            mgr = users_by_email.get(mgr_email.strip().lower())
            if mgr and u.manager_id != mgr.id:
                u.manager_id = mgr.id

    # 3) Profils de carrière (personas)
    if synthetic_personas:
        for spec in PERSONAS:
            u = users_by_email[spec["email"].strip().lower()]
            profil, created = _get_or_create_profil(db, u, spec)
            (summary["profils_created"] if created else summary["profils_existing"]).append(spec["name"])
    else:
        logger.info("SEED_SYNTHETIC_PERSONAS=false — profils de carrière non créés.")

    db.commit()

    # 4) Audit APRÈS commit : audit_service ouvre sa PROPRE connexion ; l'émettre
    #    pendant la transaction d'écriture ci-dessus déclencherait un verrou SQLite
    #    (un seul writer). Post-commit, aucune écriture n'est en cours.
    for uid, email, role in audit_pending:
        audit_service.log_event(
            AuditEventType.USER_CREATED, f"Compte de démo créé : {email} ({role})",
            user_id=uid, username=email, role=role)

    # 5) Offres + candidatures synthétiques (via les services : héritage des
    #    attendus depuis la Fiche, score calculé côté serveur). Après l'audit
    #    ci-dessus : plus aucune connexion d'audit n'écrit en concurrence.
    if synthetic_offers and demo_accounts:
        marc_user = users_by_email.get("marc.bennani@bmci.local")
        marc_profil = (db.scalar(select(Profil).where(Profil.user_id == marc_user.id))
                       if marc_user else None)
        fiches = _pick_offre_fiches(db, n=len(_OFFRE_PLAN))
        # Manager de l'équipe de démo (Jean-Marc) : rattache Marc + les candidats.
        jm_user = users_by_email.get("jeanmarc.dupont@bmci.local")
        jm_id = jm_user.id if jm_user else None
        if marc_profil is not None and jm_id and marc_profil.manager_id is None:
            marc_profil.manager_id = jm_id  # le collaborateur reporte au manager
        if fiches:
            offre_ids, ores = _seed_offres(db, fiches, users_by_email)
            summary["offres_created"] = ores["offres_created"]
            summary["offres_existing"] = ores["offres_existing"]
            candidate_profils, cres = _seed_candidate_profils(db, fiches, manager_id=jm_id)
            summary["candidats_created"] = cres["candidats_created"]
            summary["candidats_existing"] = cres["candidats_existing"]
            cand_res = _seed_candidatures(db, offre_ids, candidate_profils, marc_profil)
            summary["candidatures_created"] = cand_res["candidatures_created"]
            summary["candidatures_existing"] = cand_res["candidatures_existing"]
        else:
            logger.info("Aucune fiche avec ≥3 compétences — offres/candidatures non semées.")
        # Contenus de démo indépendants des fiches (catalogue, cloches, souhaits).
        summary["formations_created"] = _seed_formations(db)
        summary["notifications_created"] = _seed_notifications(db, users_by_email)
        summary["souhaits_created"] = _seed_souhaits(db, marc_profil)
        summary["carriere_created"] = _seed_carriere(db, users_by_email)
        summary["carto_created"] = _seed_carto(db)
        summary["entretiens_created"] = _seed_entretiens(db)
    elif synthetic_offers and not demo_accounts:
        logger.info("SEED_DEMO_ACCOUNTS=false — offres/candidatures non semées (créateurs manquants).")

    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    password = os.getenv("SEED_DEMO_PASSWORD", DEFAULT_DEMO_PASSWORD)
    db = SessionLocal()
    try:
        summary = seed_all(
            db, demo_accounts=settings.SEED_DEMO_ACCOUNTS,
            synthetic_personas=settings.SEED_SYNTHETIC_PERSONAS,
            synthetic_offers=settings.SEED_SYNTHETIC_OFFERS, password=password,
        )
    finally:
        db.close()

    print("=== Seed terminé (base :", settings.DB_PATH, ") ===")
    print("Comptes créés   :", summary["users_created"] or "(aucun)")
    print("Comptes déjà là :", summary["users_existing"] or "(aucun)")
    print("Profils créés   :", summary["profils_created"] or "(aucun)")
    print("Profils déjà là :", summary["profils_existing"] or "(aucun)")
    print("Offres créées   :", summary["offres_created"] or "(aucune)")
    print("Offres déjà là  :", summary["offres_existing"] or "(aucune)")
    print("Candidats créés :", summary["candidats_created"] or "(aucun)")
    print("Candidatures    : créées", summary["candidatures_created"],
          "· déjà là", summary["candidatures_existing"])
    print("Formations      :", len(summary["formations_created"]), "créées")
    print("Notifications   :", summary["notifications_created"], "créées")
    print("Souhaits        :", summary["souhaits_created"], "créés")
    print("Carrière        :", summary["carriere_created"], "éléments (stations + avis)")
    print("Cartographie    :", summary["carto_created"], "profils (pôles × familles)")
    print("Entretiens      :", summary["entretiens_created"], "créés")
    if summary["users_created"]:
        print("\nIdentifiants de démo (LOCAL/DÉMO uniquement) — mot de passe commun :", password)
        print("  ADMIN   : admin@bmci.local")
        print("  RH      : nadia.alami@bmci.local")
        print("  MANAGER : jeanmarc.dupont@bmci.local")
        print("  COLLAB  : marc.bennani@bmci.local  (managé par Jean-Marc Dupont)")


if __name__ == "__main__":
    main()
