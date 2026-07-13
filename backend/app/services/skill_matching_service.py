#!/usr/bin/env python3
"""
services/skill_matching_service.py — Matching profil ↔ poste.

RÔLE
    Fonctionnalité métier n°2. Mesure l'adéquation entre les compétences d'un
    collaborateur et celles requises par un poste :
      1) EXIGENCES — réutilise l'extraction de compétences du descriptif (n°1),
         chaque exigence étant ancrée au graphe (libellé canonique + importance).
      2) COUVERTURE — pour chaque exigence, le reranker évalue si une compétence du
         profil la couvre (score ∈ [0,1] ≥ seuil -> couverte, sinon écart).
      3) SCORE — pondéré (compétences essentielles > souhaitées).
    Sortie STRUCTURÉE (score, couvertes, écarts) directement exploitable par les
    recommandations de parcours/formation (les écarts = besoins de formation).

SÉCURITÉ
    100 % local (extraction LLM locale + reranker local). Descriptif traité en donnée.

EMPLACEMENT MVC
    Couche "services" : orchestration, sans route HTTP.
"""

import logging

from sqlalchemy.orm import Session

from app.services import skill_extraction_service, reranker_service

logger = logging.getLogger(__name__)


def _poids(importance: str | None) -> float:
    """Pondération d'une exigence : essentielle=1.0, souhaitée/autre=0.5."""
    return 1.0 if str(importance or "").lower().startswith("essent") else 0.5


def match_profile_to_job(db: Session, profil_competences: list[str],
                         poste_texte: str, seuil: float = 0.5) -> dict:
    """Calcule la correspondance profil ↔ poste. Renvoie un dict conforme à
    `schemas.skill_matching.MatchResponse`."""
    profil = [c.strip() for c in profil_competences if c and c.strip()]

    # 1) Exigences du poste (extraction n°1, ancrée au graphe).
    extraction = skill_extraction_service.extract_skills(db, poste_texte, top_k=1)
    exigences = []
    for s in extraction.get("skills", []):
        match = s["matches"][0] if s.get("matches") else None
        exigences.append({
            # libellé canonique (lien graphe) pour l'affichage…
            "competence": (match["label_fr"] if match else s["raw"]),
            # …mais phrase BRUTE extraite pour juger la couverture (plus naturelle
            # que le libellé ESCO parfois trop spécifique).
            "requete": s["raw"] or (match["label_fr"] if match else ""),
            "importance": s.get("importance") or "essentielle",
        })

    # 2) Couverture par le profil (reranker : exigence vs compétences du profil).
    #    On teste DEUX formulations de l'exigence (libellé canonique + phrase brute)
    #    et on retient la meilleure couverture — robuste aux libellés ESCO atypiques.
    couvertes, ecarts = [], []
    for ex in exigences:
        best, i_best = 0.0, -1
        if profil:
            for requete in dict.fromkeys([ex["requete"], ex["competence"]]):
                if not requete:
                    continue
                scores = reranker_service.rerank_scores(requete, profil)
                if scores:
                    i = max(range(len(scores)), key=lambda j: scores[j])
                    if scores[i] > best:
                        best, i_best = scores[i], i

        if best >= seuil and i_best >= 0:
            couvertes.append({
                "competence": ex["competence"], "importance": ex["importance"],
                "couverte_par": profil[i_best], "similarite": round(best, 2),
            })
        else:
            ecarts.append({
                "competence": ex["competence"], "importance": ex["importance"],
                "meilleure_similarite": round(best, 2),
            })

    # 3) Score pondéré.
    total = sum(_poids(e["importance"]) for e in exigences) or 1.0
    acquis = sum(_poids(c["importance"]) for c in couvertes)
    score = round(100 * acquis / total)

    logger.info("Matching : %d exigences, %d couvertes, score %d.", len(exigences), len(couvertes), score)
    return {
        "score": score,
        "competences_requises": len(exigences),
        "model": extraction.get("model", "?"),
        "couvertes": couvertes,
        "ecarts": ecarts,
    }
