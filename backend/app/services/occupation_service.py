#!/usr/bin/env python3
"""
services/occupation_service.py — Passerelles métiers depuis un ensemble de compétences.

RÔLE
    Brique RÉUTILISABLE du graphe. À partir d'un ensemble de compétences (leurs
    skill_id), renvoie les métiers du référentiel (ESCO/O*NET) qui mobilisent le
    plus ces compétences — socle des suggestions de mobilité et des recommandations
    de parcours. S'appuie sur les liens `occupation_skills` des 3 socles.

SÉCURITÉ
    100 % local (lecture SQLite). Aucune donnée ne sort.

EMPLACEMENT MVC
    Couche "services" : logique métier (lecture du graphe), sans route HTTP.
"""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.vector_search import knn_sql
from app.services.embedding_service import embed_text
from app.services import reranker_service

# KNN métiers, dialecte-agnostique (sqlite-vec MATCH / pgvector <=>).
_SQL_OCC = knn_sql(
    "o.id, o.label_fr, o.label_en, o.source",
    "vec_occupations", "vo", "occupations o ON o.id = vo.occupation_id")


def search_occupations(db: Session, query: str, k: int = 5,
                       rerank: bool | None = None) -> list[dict]:
    """Métiers les plus PROCHES sémantiquement de `query` (ex. un poste visé),
    via embeddings bge-m3 puis reranking. Chaque résultat :
    {occupation_id, metier, source, distance, score, rerank_score?}."""
    query = (query or "").strip()
    if not query:
        return []
    use_rerank = settings.RERANKER_ENABLED if rerank is None else rerank
    pool = max(k * 5, 25) if use_rerank else k

    vec = json.dumps(embed_text(query))
    rows = db.execute(text(_SQL_OCC), {"q": vec, "k": pool}).fetchall()
    cand: list[dict] = []
    for oid, label_fr, label_en, source, distance in rows:
        d = float(distance)
        cand.append({
            "occupation_id": oid, "metier": label_fr or label_en or "",
            "source": source, "distance": round(d, 4), "score": round(1.0 / (1.0 + d), 4),
        })
    if use_rerank and cand:
        scores = reranker_service.rerank_scores(query, [c["metier"] for c in cand])
        for c, s in zip(cand, scores):
            c["rerank_score"] = round(float(s), 4)
        cand.sort(key=lambda c: c["rerank_score"], reverse=True)
    return cand[:k]


def suggest_occupations(db: Session, skill_ids: list[int], k: int = 5,
                        min_shared: int = 2,
                        exclude_labels: set[str] | None = None) -> list[dict]:
    """Renvoie les `k` métiers partageant le plus de compétences avec `skill_ids`.

    Chaque résultat : {occupation_id, metier, source, competences_partagees}.
    `min_shared` = nombre minimal de compétences partagées pour qu'un métier soit
    une vraie passerelle (2 par défaut : élimine le bruit des métiers ne partageant
    qu'une compétence générique). Renvoie moins de résultats (voire aucun) si le
    profil est trop maigre — mieux vaut peu que du bruit.
    """
    ids = [int(s) for s in skill_ids if s]
    if not ids:
        return []

    # Pondération par rareté (type IDF) : une compétence partagée par PEU de métiers
    # (ex. « analyse du risque de crédit ») pèse plus qu'une compétence transversale
    # ubiquiste (ex. « négocier »). Évite que des métiers hors-sujet remontent parce
    # qu'ils partagent une compétence générique. Poids = 1/(nb de métiers requérant s).
    placeholders = ",".join(str(i) for i in ids)          # ints validés -> sûr
    rows = db.execute(text(
        f"WITH df AS (SELECT skill_id, COUNT(*) AS c FROM occupation_skills GROUP BY skill_id) "
        f"SELECT o.id, o.label_fr, o.label_en, o.source, "
        f"       SUM(1.0 / df.c) AS w, COUNT(*) AS n "
        f"FROM occupation_skills os "
        f"JOIN occupations o ON o.id = os.occupation_id "
        f"JOIN df ON df.skill_id = os.skill_id "
        f"WHERE os.skill_id IN ({placeholders}) "
        f"GROUP BY o.id HAVING COUNT(*) >= :ms "
        f"ORDER BY w DESC, n DESC, o.label_fr LIMIT :k"
    ), {"ms": min_shared, "k": max(k * 3, k)}).fetchall()

    exclude = {e.lower() for e in (exclude_labels or set())}
    out: list[dict] = []
    for oid, label_fr, label_en, source, _w, n in rows:
        metier = label_fr or label_en or ""
        if metier.lower() in exclude:
            continue
        out.append({
            "occupation_id": oid,
            "metier": metier,
            "source": source,
            "competences_partagees": int(n),
        })
        if len(out) >= k:
            break
    return out
