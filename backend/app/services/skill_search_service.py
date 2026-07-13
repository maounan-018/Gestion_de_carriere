#!/usr/bin/env python3
"""
services/skill_search_service.py — Recherche sémantique de compétences dans le graphe.

RÔLE
    Brique RÉUTILISABLE du graphe. À partir d'un texte libre (requête, phrase de CV,
    compétence extraite d'un descriptif de poste), renvoie les compétences
    canoniques les plus proches sémantiquement (embeddings bge-m3 + table
    vectorielle sqlite-vec `vec_skills`), avec un score. Cross-lingue FR↔EN.
    Socle commun de l'extraction, du matching profil↔poste et des recommandations.

SÉCURITÉ
    100 % local (embeddings Ollama + SQLite). Aucune donnée ne sort.

EMPLACEMENT MVC
    Couche "services" : logique métier (lecture du graphe), sans route HTTP.
"""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embedding_service import embed_text


def search_skills(db: Session, query: str, k: int = 5,
                  max_distance: float | None = None) -> list[dict]:
    """Renvoie les `k` compétences canoniques les plus proches de `query`.

    Chaque résultat : {skill_id, label_fr, label_en, skill_type, distance, score}.
    `score` = 1/(1+distance) (∈ ]0,1], décroissant avec la distance L2) pour un
    tri/seuil lisible par les autres briques. `max_distance` filtre les résultats
    trop lointains (bruit).
    """
    query = (query or "").strip()
    if not query:
        return []

    vec = json.dumps(embed_text(query))
    rows = db.execute(
        text(
            "SELECT s.id, s.label_fr, s.label_en, s.skill_type, vk.distance "
            "FROM vec_skills vk JOIN skills s ON s.id = vk.skill_id "
            "WHERE vk.embedding MATCH :q AND k = :k "
            "ORDER BY vk.distance"
        ),
        {"q": vec, "k": k},
    ).fetchall()

    out: list[dict] = []
    for sid, label_fr, label_en, skill_type, distance in rows:
        dist = float(distance)
        if max_distance is not None and dist > max_distance:
            continue
        out.append({
            "skill_id": sid,
            "label_fr": label_fr,
            "label_en": label_en,
            "skill_type": skill_type,
            "distance": round(dist, 4),
            "score": round(1.0 / (1.0 + dist), 4),
        })
    return out
