#!/usr/bin/env python3
"""
services/fiche_extraction_service.py — Extraction de compétences d'une FICHE DE POSTE.

RÔLE
    Exploite la STRUCTURE de la fiche BMCI (gabarit éditable, fiche_config_service) :
    chaque rubrique est traitée selon son "kind" —
      - metadata   -> identification (famille, périmètre, code, intitulé) ;
      - skill_list -> compétences DÉJÀ nommées (métiers/comportementales/…) -> ancrage
                      direct dans le graphe, avec la CATÉGORIE déclarée par la fiche ;
      - freetext   -> mission / activités -> le LLM en extrait les compétences implicites
                      (réutilise skill_extraction_service) puis ancrage ;
      - languages  -> langues + niveau ;
      - kpi        -> indicateurs de performance (contexte).
    Le grand gain : la fiche sépare déjà les compétences par type -> ancrage plus
    précis et sortie JSON typée, réexploitable par le matching et les recommandations.

SÉCURITÉ
    100 % local. Chaque texte de rubrique est traité comme DONNÉE (anti-injection
    via fence() dans l'extraction LLM).

EMPLACEMENT MVC
    Couche "services" : orchestration (gabarit + IA + graphe), sans route HTTP.
"""

import re
import logging

from sqlalchemy.orm import Session

from app.services import fiche_config_service, skill_extraction_service
from app.services.skill_search_service import search_skills

logger = logging.getLogger(__name__)

_LANG_RE = re.compile(r"^\s*(?P<langue>[^\(\):\-–]+?)\s*[\(:\-–]\s*(?P<niveau>[^\)]+?)\)?\s*$")


def _lines(value: str) -> list[str]:
    """Découpe une rubrique en items (une compétence par ligne / puce / point-virgule),
    en retirant puces et numérotations."""
    items = []
    for raw in re.split(r"[\n;]+", value or ""):
        item = re.sub(r"^\s*(?:[-•*–▪·]|\d+[.)])\s*", "", raw).strip()
        if item:
            items.append(item)
    return items


def _parse_languages(value: str) -> list[dict]:
    """« Français (courant) » -> {langue, niveau}."""
    out = []
    for line in _lines(value):
        m = _LANG_RE.match(line)
        if m:
            out.append({"langue": m.group("langue").strip(), "niveau": m.group("niveau").strip()})
        else:
            out.append({"langue": line, "niveau": None})
    return out


def _anchor(db: Session, libelle: str, categorie: str | None, section: str,
            implicite: bool, top_k: int) -> dict:
    """Rapproche une compétence (nommée ou extraite) des compétences canoniques du graphe."""
    return {
        "libelle": libelle,
        "categorie": categorie,          # catégorie DÉCLARÉE par la fiche (signal fort)
        "source_section": section,
        "implicite": implicite,          # True = déduite d'un texte libre (mission/activités)
        "matches": search_skills(db, libelle, k=top_k),
    }


def extract_from_fiche(db: Session, sections: dict, top_k: int = 1) -> dict:
    """Extrait, à partir d'une fiche (dict {clé_section: texte}), les métadonnées du
    poste + les compétences typées ancrées au graphe + langues + indicateurs.
    `sections` suit le gabarit (fiche_config_service) ; les rubriques absentes sont ignorées."""
    poste: dict = {}
    competences: list[dict] = []
    langues: list[dict] = []
    indicateurs: list[str] = []

    for sec in fiche_config_service.get_sections():
        key, kind = sec["key"], sec["kind"]
        value = (sections.get(key) or "").strip()
        if not value:
            continue

        if kind == "metadata":
            poste[key] = value
        elif kind == "kpi":
            indicateurs.extend(_lines(value))
        elif kind == "languages":
            langues.extend(_parse_languages(value))
        elif kind == "skill_list":
            for item in _lines(value):
                competences.append(_anchor(db, item, sec.get("categorie"), key, False, top_k))
        elif kind == "freetext":
            res = skill_extraction_service.extract_skills(db, value, top_k=top_k)
            for s in res.get("skills", []):
                competences.append({
                    "libelle": s["raw"], "categorie": sec.get("categorie"),
                    "source_section": key, "implicite": True, "matches": s["matches"],
                })

    logger.info("Fiche : %d compétences (%d rubriques traitées), %d langue(s).",
                len(competences), len([s for s in fiche_config_service.get_sections()
                                       if (sections.get(s["key"]) or "").strip()]), len(langues))
    return {
        "poste": poste,
        "competences": competences,
        "langues": langues,
        "indicateurs_performance": indicateurs,
    }
