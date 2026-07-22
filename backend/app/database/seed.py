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

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User, Role, UserType
from app.models.profil import Profil, ProfilCompetence, CompetenceSource
from app.models.fiche import FicheCompetence
from app.models.audit_log import AuditEventType
from app.services import audit_service

logger = logging.getLogger(__name__)

# Mot de passe de démo COMMUN (local/démo uniquement). Surchargable par env.
DEFAULT_DEMO_PASSWORD = "Bmci-Demo-2026!"

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


def seed_all(db: Session, *, demo_accounts: bool, synthetic_personas: bool,
             password: str) -> dict:
    """Amorce comptes + profils selon les leviers. Idempotent. Renvoie un résumé."""
    summary = {"users_created": [], "users_existing": [], "profils_created": [], "profils_existing": []}

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

    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    password = os.getenv("SEED_DEMO_PASSWORD", DEFAULT_DEMO_PASSWORD)
    db = SessionLocal()
    try:
        summary = seed_all(
            db, demo_accounts=settings.SEED_DEMO_ACCOUNTS,
            synthetic_personas=settings.SEED_SYNTHETIC_PERSONAS, password=password,
        )
    finally:
        db.close()

    print("=== Seed terminé (base :", settings.DB_PATH, ") ===")
    print("Comptes créés   :", summary["users_created"] or "(aucun)")
    print("Comptes déjà là :", summary["users_existing"] or "(aucun)")
    print("Profils créés   :", summary["profils_created"] or "(aucun)")
    print("Profils déjà là :", summary["profils_existing"] or "(aucun)")
    if summary["users_created"]:
        print("\nIdentifiants de démo (LOCAL/DÉMO uniquement) — mot de passe commun :", password)
        print("  ADMIN   : admin@bmci.local")
        print("  RH      : nadia.alami@bmci.local")
        print("  MANAGER : jeanmarc.dupont@bmci.local")
        print("  COLLAB  : marc.bennani@bmci.local  (managé par Jean-Marc Dupont)")


if __name__ == "__main__":
    main()
