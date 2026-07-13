#!/usr/bin/env python3
"""
services/referentiels/onet_loader.py — Ingestion du référentiel O*NET (US).

RÔLE
    Charge O*NET 30.3 (format texte tab-séparé) dans le graphe de compétences :
      - Occupations (métiers)           <- "Occupation Data.txt"
      - Compétences + savoirs (nœuds)   <- "Content Model Reference.txt" (2.A/2.B/2.C)
      - Liens métier↔compétence         <- "Essential/Transferable Skills.txt", "Knowledge.txt"
                                            (échelle IM = Importance, seuil configurable)
    Chaque compétence O*NET est aussi tracée dans le crosswalk (SkillMapping,
    source=ONET, external_id = Element ID) pour l'alignement futur avec ESCO.

    O*NET est en anglais : label_fr reçoit provisoirement l'anglais (à traduire
    ensuite via le LLM lc-redacteur). Idempotent : ne recharge pas si déjà présent.

SÉCURITÉ / LICENCE
    Données publiques (Creative Commons BY 4.0, U.S. DOL/ETA). 100 % local.

EMPLACEMENT MVC
    Couche "services" : logique d'ingestion, sans route HTTP.
"""

import os
import csv
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import attributions
from app.models.referential import ReferentialSource, SourceCode
from app.models.skill import Skill, SkillType
from app.models.occupation import Occupation, OccupationSkill, SkillRequirement
from app.models.skill_mapping import SkillMapping, MappingMethod

logger = logging.getLogger(__name__)

ONET_VERSION = "30.3"
IMPORTANCE_MIN = 3.0        # seuil de rattachement métier↔compétence (IM 1..5)
ESSENTIAL_MIN = 3.67       # au-delà : compétence "essentielle" au métier

# Fichiers de notation (occupation × élément) à parcourir pour les liens.
_RATING_FILES = ["Essential Skills.txt", "Transferable Skills.txt", "Knowledge.txt"]


def _data_dir() -> str:
    """Trouve le dossier O*NET contenant 'Occupation Data.txt' (robuste au
    sous-dossier de version, ex. db_30_3_text)."""
    base = os.path.join(settings.REFERENTIELS_DIR, "onet")
    for root, _dirs, files in os.walk(base):
        if "Occupation Data.txt" in files:
            return root
    raise FileNotFoundError(f"Données O*NET introuvables sous {base} (lancez le téléchargement).")


def _read_tsv(path: str):
    """Itère les lignes d'un fichier O*NET tab-séparé en dictionnaires {colonne: valeur}."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            yield row


def _is_leaf_skill(element_id: str) -> str | None:
    """Renvoie le type de compétence si l'Element ID est une FEUILLE nommée
    (ex. 2.A.1.a), sinon None (catégories 2.A, 2.A.1 exclues)."""
    parts = element_id.split(".")
    if len(parts) < 4:            # feuilles seulement (catégories = 2 ou 3 segments)
        return None
    if element_id.startswith(("2.A", "2.B")):
        return SkillType.SKILL if element_id.startswith("2.A") else SkillType.TRANSVERSAL
    if element_id.startswith("2.C"):
        return SkillType.KNOWLEDGE
    return None


def load_onet(db: Session) -> dict:
    """Ingestion complète O*NET → graphe. Renvoie un dict de comptes.
    Idempotent : si la source ONET est déjà enregistrée, on ne recharge pas."""
    if db.scalar(select(ReferentialSource).where(ReferentialSource.code == SourceCode.ONET)):
        logger.info("O*NET déjà ingéré — saut.")
        return {"skipped": True}

    data = _data_dir()
    logger.info("Ingestion O*NET depuis %s", data)

    # 1) Compétences + savoirs (nœuds) depuis la taxonomie Content Model.
    element_to_skill: dict[str, Skill] = {}
    for row in _read_tsv(os.path.join(data, "Content Model Reference.txt")):
        eid = (row.get("Element ID") or "").strip()
        stype = _is_leaf_skill(eid)
        if not stype:
            continue
        name = (row.get("Element Name") or "").strip()
        desc = (row.get("Description") or "").strip() or None
        skill = Skill(
            label_fr=name, label_en=name,        # FR provisoire = EN (traduction ultérieure)
            description_fr=desc, description_en=desc,
            skill_type=stype,
        )
        db.add(skill)
        element_to_skill[eid] = skill
    db.flush()  # attribue les IDs
    logger.info("  %d compétences/savoirs créés", len(element_to_skill))

    # Crosswalk : chaque compétence O*NET tracée (source=ONET, external_id=Element ID).
    for eid, skill in element_to_skill.items():
        db.add(SkillMapping(skill_id=skill.id, source=SourceCode.ONET,
                            external_id=eid, external_label=skill.label_en,
                            confidence=1.0, method=MappingMethod.EXACT, validated=True))

    # 2) Occupations (métiers).
    soc_to_occ: dict[str, Occupation] = {}
    for row in _read_tsv(os.path.join(data, "Occupation Data.txt")):
        soc = (row.get("O*NET-SOC Code") or "").strip()
        if not soc:
            continue
        occ = Occupation(
            label_fr=(row.get("Title") or "").strip(), label_en=(row.get("Title") or "").strip(),
            description_fr=(row.get("Description") or "").strip() or None,
            description_en=(row.get("Description") or "").strip() or None,
            source=SourceCode.ONET, code=soc, source_uri=None,
        )
        db.add(occ)
        soc_to_occ[soc] = occ
    db.flush()
    logger.info("  %d métiers créés", len(soc_to_occ))

    # 3) Liens métier↔compétence (Importance >= seuil), dé-dupliqués.
    seen: set[tuple[int, int]] = set()
    n_links = 0
    for fname in _RATING_FILES:
        path = os.path.join(data, fname)
        if not os.path.exists(path):
            continue
        for row in _read_tsv(path):
            if (row.get("Scale ID") or "").strip() != "IM":
                continue
            try:
                value = float(row.get("Data Value") or 0)
            except ValueError:
                continue
            if value < IMPORTANCE_MIN:
                continue
            occ = soc_to_occ.get((row.get("O*NET-SOC Code") or "").strip())
            skill = element_to_skill.get((row.get("Element ID") or "").strip())
            if not occ or not skill:
                continue
            key = (occ.id, skill.id)
            if key in seen:
                continue
            seen.add(key)
            db.add(OccupationSkill(
                occupation_id=occ.id, skill_id=skill.id,
                requirement=SkillRequirement.ESSENTIAL if value >= ESSENTIAL_MIN else SkillRequirement.OPTIONAL,
            ))
            n_links += 1
    logger.info("  %d liens métier↔compétence créés", n_links)

    # 4) Enregistre la source (journal d'ingestion).
    db.add(ReferentialSource(
        code=SourceCode.ONET, name="O*NET (U.S. DOL/ETA)", version=ONET_VERSION,
        languages="en", license="CC-BY-4.0", attribution=attributions.ONET,
        imported_at=datetime.now(timezone.utc),
        n_skills=len(element_to_skill), n_occupations=len(soc_to_occ),
    ))
    db.commit()

    counts = {"skills": len(element_to_skill), "occupations": len(soc_to_occ), "links": n_links}
    logger.info("O*NET ingéré: %s", counts)
    return counts
