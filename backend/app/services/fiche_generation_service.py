#!/usr/bin/env python3
"""
services/fiche_generation_service.py — Génération de FICHES DE POSTE (compétences inférées).

RÔLE
    À partir d'un métier et de son département (cartographie BMCI), GÉNÈRE une fiche
    de poste structurée selon le gabarit, avec des compétences INFÉRÉES. Méthode
    ancrée (zéro compétence hors-sol) :
      1) ANCRAGE GRAPHE — on rapproche le métier des occupations ESCO/O*NET proches
         (occupation_service) et on récupère leurs compétences ESSENTIELLES du
         référentiel : ce sont les compétences de RÉFÉRENCE à privilégier.
      2) RÉDACTION — le meilleur modèle FR (mistral-nemo, tâche "generation_fiche")
         rédige la fiche (mission, activités, compétences par catégorie, langues, KPI)
         en s'APPUYANT sur ces compétences de référence.
    Sortie = une fiche au FORMAT DU GABARIT, directement consommable par l'extraction
    et le matching. ⚠️ Contenu SYNTHÉTIQUE (rôles-types) — jamais des données réelles.

SÉCURITÉ
    100 % local. Données de test/générées explicitement marquées `synthetique=True`.

EMPLACEMENT MVC
    Couche "services" : orchestration (graphe + IA), sans route HTTP.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services import occupation_service
from app.services.ai_router import generate

logger = logging.getLogger(__name__)

_TASK = "generation_fiche"

_SYSTEM = (
    "Tu es un expert RH d'une banque marocaine (BMCI, groupe BNP Paribas). Tu rédiges "
    "une FICHE DE POSTE réaliste, concise et professionnelle, en FRANÇAIS.\n"
    "On te donne un métier, son département, et des COMPÉTENCES DE RÉFÉRENCE issues d'un "
    "référentiel officiel : appuie-toi dessus en priorité, n'invente pas de compétences farfelues.\n"
    "Réponds STRICTEMENT en JSON (aucun texte autour), au format EXACT :\n"
    '{"mission": "2 à 3 phrases", '
    '"activites_principales": ["…"], '  # 4 à 6
    '"competences_metiers": ["…"], '  # 4 à 7 savoir-faire techniques du métier
    '"competences_comportementales": ["…"], '  # 3 à 5 savoir-être
    '"competences_transversales": ["…"], '  # 2 à 4
    '"methodologie_outils_technologies": ["…"], '  # 2 à 5 outils / méthodo / techno
    '"langues": ["Français (courant)", "…"], '
    '"indicateurs_performances": ["…"]}\n'  # 2 à 4 KPI
    "Chaque compétence est COURTE (2 à 6 mots), normalisée, réaliste pour une banque."
)


def _grounded_skills(db: Session, metier: str, top_occ: int = 3, limit: int = 18) -> list[str]:
    """Compétences ESSENTIELLES des occupations ESCO/O*NET les plus proches du métier
    (compétences de référence pour ancrer la génération)."""
    occs = occupation_service.search_occupations(db, metier, k=top_occ)
    ids = [int(o["occupation_id"]) for o in occs]
    if not ids:
        return []
    placeholders = ",".join(str(i) for i in ids)  # ints validés -> sûr
    rows = db.execute(
        text(
            f"SELECT DISTINCT s.label_fr FROM occupation_skills os "
            f"JOIN skills s ON s.id = os.skill_id "
            f"WHERE os.occupation_id IN ({placeholders}) AND os.requirement = 'essential' "
            f"AND s.canonical = 1 AND s.label_fr IS NOT NULL LIMIT :n"
        ),
        {"n": limit},
    ).fetchall()
    return [r[0] for r in rows]


def _lines(value) -> str:
    """Liste -> texte (une entrée par ligne), format attendu par le gabarit/extraction."""
    if isinstance(value, list):
        return "\n".join(str(x).strip() for x in value if str(x).strip())
    return str(value or "").strip()


def _code_poste(metier: str) -> str:
    """Code poste SYNTHÉTIQUE : 6 chiffres stables (hash) + désignation = intitulé."""
    num = 100000 + (abs(hash(metier)) % 900000)
    return f"{num} - {metier}"


def generate_fiche(db: Session, metier: str, departement: dict) -> dict:
    """Génère une fiche de poste (sections du gabarit) pour un métier d'un département.
    `departement` = entrée de config/departements_metiers.yaml ({nom, pole, ...})."""
    grounded = _grounded_skills(db, metier)
    ref = (
        "\n- ".join(grounded)
        if grounded
        else "(aucune — appuie-toi sur ta connaissance du métier bancaire)"
    )
    prompt = (
        f"Métier : {metier}\n"
        f"Département : {departement.get('nom', '')} (pôle : {departement.get('pole', '')})\n"
        f"Banque : BMCI (Maroc).\n\n"
        f"COMPÉTENCES DE RÉFÉRENCE à privilégier :\n- {ref}\n\n"
        "Rédige la fiche de poste au format JSON demandé."
    )
    result = generate(
        _TASK,
        prompt,
        system=_SYSTEM,
        is_valid=lambda r: isinstance(r, dict)
        and r.get("mission")
        and r.get("competences_metiers"),
    )

    sections = {
        "famille_metier": departement.get("pole", ""),
        "perimetre_bmci": departement.get("nom", ""),
        "code_poste": _code_poste(metier),
        "intitule_poste": metier,
        "mission": _lines(result.get("mission")),
        "activites_principales": _lines(result.get("activites_principales")),
        "competences_metiers": _lines(result.get("competences_metiers")),
        "competences_comportementales": _lines(result.get("competences_comportementales")),
        "competences_transversales": _lines(result.get("competences_transversales")),
        "langues": _lines(result.get("langues")) or "Français (courant)\nAnglais (professionnel)",
        "methodologie_outils_technologies": _lines(result.get("methodologie_outils_technologies")),
        "indicateurs_performances": _lines(result.get("indicateurs_performances")),
    }
    logger.info(
        "Fiche générée (SYNTHÉTIQUE) : %s — %d compétences réf. utilisées.", metier, len(grounded)
    )
    return {
        "metier": metier,
        "departement": departement.get("nom", ""),
        "synthetique": True,  # ⚠️ contenu généré, jamais des données réelles
        "sections": sections,
        "competences_reference": grounded,
    }
