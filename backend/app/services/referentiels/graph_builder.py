#!/usr/bin/env python3
"""
services/referentiels/graph_builder.py — Vectorisation du graphe de compétences.

RÔLE
    Après le chargement d'un référentiel, calcule l'embedding (bge-m3) de chaque
    compétence encore non vectorisée et l'insère dans la table sqlite-vec
    `vec_skills` (clé = Skill.id). Ces vecteurs alimentent le matching sémantique
    et le crosswalk inter-référentiels. Fournit aussi un état du graphe.

EMPLACEMENT MVC
    Couche "services" : logique métier (vectorisation), sans route HTTP.
"""

import json
import logging

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.occupation import Occupation, OccupationSkill
from app.services.embedding_service import embed_text

logger = logging.getLogger(__name__)


def _skill_text(s: Skill) -> str:
    """Texte représentatif d'une compétence pour l'embedding (bilingue + définition)."""
    parts = [s.label_fr or "", s.label_en or ""]
    if s.description_en:
        parts.append(s.description_en)
    # dé-doublonne label_fr/label_en identiques (cas O*NET)
    seen, out = set(), []
    for p in parts:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return " — ".join(out)


def embed_missing_skills(db: Session, commit_every: int = 200) -> int:
    """Embedde et stocke dans vec_skills toutes les compétences qui n'ont pas
    encore de vecteur. Renvoie le nombre de compétences vectorisées."""
    existing = {r[0] for r in db.execute(text("SELECT skill_id FROM vec_skills"))}
    skills = db.scalars(select(Skill)).all()
    todo = [s for s in skills if s.id not in existing]
    logger.info("Vectorisation : %d compétences à embedder (%d déjà faites).", len(todo), len(existing))

    n = 0
    for s in todo:
        vector = embed_text(_skill_text(s))
        db.execute(
            text("INSERT INTO vec_skills(skill_id, embedding) VALUES (:id, :emb)"),
            {"id": s.id, "emb": json.dumps(vector)},
        )
        n += 1
        if n % commit_every == 0:
            db.commit()
            logger.info("  … %d/%d vectorisées", n, len(todo))
    db.commit()
    logger.info("Vectorisation terminée : %d nouvelles compétences.", n)
    return n


def graph_stats(db: Session) -> dict:
    """État du graphe (pour vérification/monitoring)."""
    return {
        "skills": db.scalar(select(func.count()).select_from(Skill)),
        "occupations": db.scalar(select(func.count()).select_from(Occupation)),
        "occupation_skill_links": db.scalar(select(func.count()).select_from(OccupationSkill)),
        "vectors": db.execute(text("SELECT count(*) FROM vec_skills")).scalar(),
    }
