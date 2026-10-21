#!/usr/bin/env python3
"""
services/referentiels/esco_loader.py — Ingestion du référentiel ESCO (pivot UE, FR/EN).

RÔLE
    Charge ESCO v1.2.1 (CSV classification) — le PIVOT multilingue — dans le graphe :
      - Compétences bilingues (jointure EN↔FR par conceptUri)  <- skills_{en,fr}.csv
      - Métiers bilingues                                       <- occupations_{en,fr}.csv
      - Liens métier↔compétence (essential/optional)           <- occupationSkillRelations_en.csv
      - Hiérarchie des compétences (broader/narrower)          <- broaderRelationsSkillPillar_en.csv
      - Liens transversaux compétence↔compétence               <- skillSkillRelations_en.csv
    Chaque compétence ESCO est tracée dans le crosswalk (SkillMapping, source=ESCO,
    external_id = conceptUri) — c'est le socle sur lequel O*NET/SFIA seront alignés.

    Parsing CSV robuste (champs entre guillemets, virgules et retours-ligne inclus).
    Insertions en masse pour tenir les volumes (~14k compétences, ~126k liens).
    Idempotent : ne recharge pas si ESCO déjà présent.

SÉCURITÉ / LICENCE
    Données publiques (Décision 2011/833/UE, réutilisation libre). 100 % local.
    Mention d'attribution obligatoire posée sur la source (voir core/attributions).

EMPLACEMENT MVC
    Couche "services" : logique d'ingestion, sans route HTTP.
"""

import csv
import logging
import os
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import attributions
from app.core.config import settings
from app.models.occupation import Occupation, OccupationSkill, SkillRequirement
from app.models.referential import ReferentialSource, SourceCode
from app.models.skill import RelationType, Skill, SkillRelation, SkillType
from app.models.skill_mapping import MappingMethod, SkillMapping

logger = logging.getLogger(__name__)

ESCO_VERSION = "1.2.1"
csv.field_size_limit(10 * 1024 * 1024)  # définitions longues


def _find_dir(lang: str) -> str:
    """Trouve le dossier CSV d'une langue (contenant skills_<lang>.csv)."""
    base = settings.REFERENTIELS_DIR
    target = f"skills_{lang}.csv"
    for root, _dirs, files in os.walk(base):
        if target in files and "esco" in root.lower():
            return root
    raise FileNotFoundError(f"CSV ESCO ({lang}) introuvables sous {base}.")


def _rows(path: str):
    with open(path, encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def _skill_type(esco_type: str | None) -> str:
    t = (esco_type or "").lower()
    if "knowledge" in t:
        return SkillType.KNOWLEDGE
    if "skill" in t or "competence" in t:
        return SkillType.SKILL
    return SkillType.OTHER


def load_esco(db: Session) -> dict:
    """Ingestion complète ESCO → graphe. Renvoie un dict de comptes.
    N.B. : la VECTORISATION est faite séparément (graph_builder), car longue (~14k)."""
    if db.scalar(select(ReferentialSource).where(ReferentialSource.code == SourceCode.ESCO)):
        logger.info("ESCO déjà ingéré — saut.")
        return {"skipped": True}

    dir_en, dir_fr = _find_dir("en"), _find_dir("fr")
    logger.info("Ingestion ESCO — EN=%s", dir_en)

    # 1) Compétences : index FR par conceptUri, puis parcours EN (jointure).
    fr_skills = {r["conceptUri"]: r for r in _rows(os.path.join(dir_fr, "skills_fr.csv"))}
    uri_to_skill: dict[str, Skill] = {}
    for r in _rows(os.path.join(dir_en, "skills_en.csv")):
        uri = r.get("conceptUri")
        if not uri:
            continue
        rf = fr_skills.get(uri, {})
        label_en = (r.get("preferredLabel") or "").strip()
        label_fr = (rf.get("preferredLabel") or "").strip() or label_en
        skill = Skill(
            label_fr=label_fr[:300],
            label_en=label_en[:300],
            description_fr=(rf.get("description") or "").strip() or None,
            description_en=(r.get("description") or "").strip() or None,
            skill_type=_skill_type(r.get("skillType")),
        )
        db.add(skill)
        uri_to_skill[uri] = skill
    db.flush()
    logger.info("  %d compétences (FR/EN)", len(uri_to_skill))

    db.bulk_insert_mappings(
        SkillMapping,
        [
            {
                "skill_id": s.id,
                "source": SourceCode.ESCO,
                "external_id": uri,
                "external_label": s.label_en,
                "confidence": 1.0,
                "method": MappingMethod.EXACT,
                "validated": True,
            }
            for uri, s in uri_to_skill.items()
        ],
    )

    # 2) Métiers (jointure EN/FR par conceptUri).
    fr_occ = {r["conceptUri"]: r for r in _rows(os.path.join(dir_fr, "occupations_fr.csv"))}
    uri_to_occ: dict[str, Occupation] = {}
    for r in _rows(os.path.join(dir_en, "occupations_en.csv")):
        uri = r.get("conceptUri")
        if not uri:
            continue
        rf = fr_occ.get(uri, {})
        label_en = (r.get("preferredLabel") or "").strip()
        occ = Occupation(
            label_fr=(rf.get("preferredLabel") or "").strip()[:300] or label_en[:300],
            label_en=label_en[:300],
            description_fr=(rf.get("description") or "").strip() or None,
            description_en=(r.get("description") or "").strip() or None,
            source=SourceCode.ESCO,
            source_uri=uri,
            code=(r.get("code") or r.get("iscoGroup") or "").strip() or None,
        )
        db.add(occ)
        uri_to_occ[uri] = occ
    db.flush()
    logger.info("  %d métiers (FR/EN)", len(uri_to_occ))

    # 3) Liens métier↔compétence (essential/optional).
    links = []
    seen = set()
    for r in _rows(os.path.join(dir_en, "occupationSkillRelations_en.csv")):
        occ = uri_to_occ.get(r.get("occupationUri"))
        skill = uri_to_skill.get(r.get("skillUri"))
        if not occ or not skill or (occ.id, skill.id) in seen:
            continue
        seen.add((occ.id, skill.id))
        req = (
            SkillRequirement.ESSENTIAL
            if (r.get("relationType") or "").strip() == "essential"
            else SkillRequirement.OPTIONAL
        )
        links.append({"occupation_id": occ.id, "skill_id": skill.id, "requirement": req})
    db.bulk_insert_mappings(OccupationSkill, links)
    logger.info("  %d liens métier↔compétence", len(links))

    # 4) Hiérarchie (broader) + 5) relations transversales (related).
    rels, seen_r = [], set()

    def _add_rel(parent, child, rtype):
        p, c = uri_to_skill.get(parent), uri_to_skill.get(child)
        if not p or not c or (p.id, c.id, rtype) in seen_r:
            return
        seen_r.add((p.id, c.id, rtype))
        rels.append({"parent_id": p.id, "child_id": c.id, "relation_type": rtype})

    for r in _rows(os.path.join(dir_en, "broaderRelationsSkillPillar_en.csv")):
        _add_rel(r.get("broaderUri"), r.get("conceptUri"), RelationType.BROADER)
    skillskill = os.path.join(dir_en, "skillSkillRelations_en.csv")
    if os.path.exists(skillskill):
        for r in _rows(skillskill):
            _add_rel(r.get("originalSkillUri"), r.get("relatedSkillUri"), RelationType.RELATED)
    db.bulk_insert_mappings(SkillRelation, rels)
    logger.info("  %d relations entre compétences", len(rels))

    # 6) Source + attribution.
    db.add(
        ReferentialSource(
            code=SourceCode.ESCO,
            name="ESCO (Commission européenne)",
            version=ESCO_VERSION,
            languages="fr,en",
            license="EUPL-1.2",
            attribution=attributions.ESCO,
            imported_at=datetime.now(UTC),
            n_skills=len(uri_to_skill),
            n_occupations=len(uri_to_occ),
        )
    )
    db.commit()

    counts = {
        "skills": len(uri_to_skill),
        "occupations": len(uri_to_occ),
        "links": len(links),
        "relations": len(rels),
    }
    logger.info("ESCO ingéré: %s", counts)
    return counts
