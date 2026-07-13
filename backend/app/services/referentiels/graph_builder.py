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
from app.services.embedding_service import embed_batch

logger = logging.getLogger(__name__)


def _skill_text(s: Skill) -> str:
    """Texte représentatif d'une compétence pour l'embedding (bilingue + définition).
    Garantit un texte NON VIDE (fallback), sinon Ollama /api/embed renvoie 400."""
    parts = [s.label_fr or "", s.label_en or "", s.description_fr or "", s.description_en or ""]
    seen, out = set(), []
    for p in parts:
        p = (p or "").strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return " — ".join(out) if out else "compétence"


def embed_missing_skills(db: Session, batch_size: int = 128) -> int:
    """Embedde (PAR LOTS) et stocke dans vec_skills toutes les compétences sans
    vecteur. Renvoie le nombre de compétences vectorisées. `batch_size` = granularité
    de commit DB ; l'embedding lui-même se fait par sous-lots de 64 (repli adaptatif)."""
    existing = {r[0] for r in db.execute(text("SELECT skill_id FROM vec_skills"))}
    todo = [s for s in db.scalars(select(Skill)).all() if s.id not in existing]
    logger.info("Vectorisation : %d compétences à embedder (%d déjà faites).", len(todo), len(existing))

    ins = text("INSERT INTO vec_skills(skill_id, embedding) VALUES (:id, :emb)")
    n = 0
    for i in range(0, len(todo), batch_size):
        chunk = todo[i:i + batch_size]
        vectors = embed_batch([_skill_text(s) for s in chunk], batch_size=64)
        db.execute(ins, [{"id": s.id, "emb": json.dumps(v)} for s, v in zip(chunk, vectors)])
        db.commit()
        n += len(chunk)
        logger.info("  … %d/%d vectorisées", n, len(todo))
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
