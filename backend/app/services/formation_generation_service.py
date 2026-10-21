#!/usr/bin/env python3
"""
services/formation_generation_service.py — Génération de FORMATIONS synthétiques (LMS).

RÔLE
    Pas d'accès au LMS réel : à la place, on GÉNÈRE (LLM local) une proposition de
    formation SYNTHÉTIQUE ciblant une compétence à développer — pour démontrer la
    recommandation (répondre à un écart de compétence par une formation concrète).
    Le libellé de compétence est ANCRÉ sur le référentiel (compétence canonique la
    plus proche) avant génération, pour rester cohérent avec le graphe.

ÉTIQUETAGE
    Contenu explicitement `synthetique=True` — jamais présenté comme un cours réel.

EMPLACEMENT MVC
    Couche "services" : orchestration (graphe + IA), sans route HTTP ni écriture DB
    (la persistance au catalogue est faite par `formation_service`).
"""

import logging

from sqlalchemy.orm import Session

from app.services.ai_router import generate
from app.services.skill_search_service import search_skills

logger = logging.getLogger(__name__)

_TASK = "generation_formation"

_SYSTEM = (
    "Tu es un ingénieur pédagogique d'une banque (BMCI, groupe BNP Paribas). On te "
    "donne une COMPÉTENCE à développer ; tu proposes une FORMATION synthétique réaliste, "
    "en FRANÇAIS, adaptée au secteur bancaire. N'invente pas d'organisme réel précis.\n"
    "Réponds STRICTEMENT en JSON (aucun texte autour), au format EXACT :\n"
    '{"titre": "…", "organisme": "…", "duree": "ex. 14 h", '
    '"niveau": "Débutant"|"Intermédiaire"|"Avancé", "domaine": "…", '
    '"objectifs": ["…"], "modules": ["…"], "tags": ["…"]}\n'
    "Titre court et concret ; 3 à 5 objectifs ; 3 à 6 modules ; 2 à 5 tags."
)


def _is_valid(r) -> bool:
    return isinstance(r, dict) and bool(r.get("titre")) and isinstance(r.get("modules"), list)


def _lst(v) -> list[str]:
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []


def generer(db: Session, competence: str) -> dict:
    """Génère une formation SYNTHÉTIQUE ciblant `competence`. Ancre d'abord le libellé
    sur la compétence canonique la plus proche du référentiel. Repli propre si l'IA
    est indisponible (titre par défaut fondé sur la compétence)."""
    comp = (competence or "").strip()
    matches = search_skills(db, comp, k=1)
    cible = matches[0]["label_fr"] if matches else comp
    prompt = (
        f"Compétence à développer : {cible}\n"
        f"(saisie de l'utilisateur : « {comp} »)\nBanque : BMCI (Maroc).\n\n"
        "Propose la formation au format JSON demandé."
    )
    try:
        r = generate(_TASK, prompt, system=_SYSTEM, is_valid=_is_valid)
    except Exception as e:
        logger.warning("Génération de formation indisponible (%s).", e)
        r = {}
    r = r if isinstance(r, dict) else {}
    logger.info("Formation générée (SYNTHÉTIQUE) pour : %s", cible)
    return {
        "titre": (r.get("titre") or f"Formation : {cible}").strip(),
        "organisme": (r.get("organisme") or "Académie interne BMCI").strip() or None,
        "duree": (r.get("duree") or None),
        "niveau": (r.get("niveau") or None),
        "domaine": (r.get("domaine") or None),
        "skill_cible": cible,
        "objectifs": _lst(r.get("objectifs")),
        "modules": _lst(r.get("modules")),
        "tags": _lst(r.get("tags")),
        "synthetique": True,
    }
