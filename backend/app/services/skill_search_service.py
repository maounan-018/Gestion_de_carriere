#!/usr/bin/env python3
"""
services/skill_search_service.py — Recherche sémantique de compétences dans le graphe.

RÔLE
    Brique RÉUTILISABLE du graphe. À partir d'un texte libre (requête, phrase de CV,
    compétence extraite d'un descriptif), renvoie les compétences canoniques les
    plus PERTINENTES, en deux temps :
      1) rappel large par embeddings bge-m3 (table vectorielle sqlite-vec) ;
      2) reclassement fin par le reranker cross-encoder (bge-reranker-v2-m3), qui
         corrige les faux amis de l'embedding seul.
    Cross-lingue FR↔EN. Socle commun de l'extraction, du matching profil↔poste et
    des recommandations.

SÉCURITÉ
    100 % local (embeddings + reranker + SQLite). Aucune donnée ne sort.

EMPLACEMENT MVC
    Couche "services" : logique métier (lecture du graphe), sans route HTTP.
"""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding_service import embed_text
from app.services import reranker_service

_SQL = (
    "SELECT s.id, s.label_fr, s.label_en, s.skill_type, "
    "       s.description_fr, s.description_en, vk.distance "
    "FROM vec_skills vk JOIN skills s ON s.id = vk.skill_id "
    "WHERE vk.embedding MATCH :q AND k = :k "
    "ORDER BY vk.distance"
)


def _passage(c: dict) -> str:
    """Texte présenté au reranker : le LIBELLÉ bilingue (fr / en) sans la définition.
    Les définitions ESCO, verbeuses, brouillent le cross-encoder sur des requêtes
    courtes (« analyse incidents »). Le libellé bilingue donne le meilleur signal."""
    fr = c["label_fr"] or ""
    en = c["label_en"] or ""
    if fr and en and fr.lower() != en.lower():
        return f"{fr} / {en}"
    return fr or en


def search_skills(db: Session, query: str, k: int = 5,
                  max_distance: float | None = None,
                  rerank: bool | None = None) -> list[dict]:
    """Renvoie les `k` compétences canoniques les plus pertinentes pour `query`.

    Chaque résultat : {skill_id, label_fr, label_en, skill_type, distance, score,
    rerank_score?}. `score` = proximité embeddings (1/(1+distance) L2). Si le
    reranking est actif, on récupère un pool élargi puis on trie par `rerank_score`
    (∈ [0,1], pertinence cross-encoder). `max_distance` élague le bruit lointain.
    """
    query = (query or "").strip()
    if not query:
        return []

    use_rerank = settings.RERANKER_ENABLED if rerank is None else rerank
    pool = max(k * 5, 25) if use_rerank else k

    vec = json.dumps(embed_text(query))
    rows = db.execute(text(_SQL), {"q": vec, "k": pool}).fetchall()

    cand: list[dict] = []
    for sid, label_fr, label_en, skill_type, dfr, den, distance in rows:
        dist = float(distance)
        if max_distance is not None and dist > max_distance:
            continue
        cand.append({
            "skill_id": sid, "label_fr": label_fr, "label_en": label_en,
            "skill_type": skill_type, "description_fr": dfr, "description_en": den,
            "distance": round(dist, 4), "score": round(1.0 / (1.0 + dist), 4),
        })

    if use_rerank and cand:
        scores = reranker_service.rerank_scores(query, [_passage(c) for c in cand])
        for c, s in zip(cand, scores):
            c["rerank_score"] = round(float(s), 4)
        cand.sort(key=lambda c: c["rerank_score"], reverse=True)

    result = cand[:k]
    for c in result:                       # descriptions verbeuses hors payload
        c.pop("description_fr", None)
        c.pop("description_en", None)
    return result
