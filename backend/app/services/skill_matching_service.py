#!/usr/bin/env python3
"""
services/skill_matching_service.py — Matching profil ↔ poste.

RÔLE
    Fonctionnalité métier n°2. Mesure l'adéquation entre les compétences d'un
    collaborateur et celles requises par un poste :
      1) EXIGENCES — réutilise l'extraction de compétences du descriptif (n°1),
         chaque exigence étant ancrée au graphe (libellé canonique + skill_id).
      2) COUVERTURE — pour chaque exigence, le reranker évalue si une compétence du
         profil la couvre (score ∈ [0,1] ≥ seuil -> couverte, sinon écart).
      3) SCORE — pondéré (compétences essentielles > souhaitées).
    Les briques `build_exigences` / `evaluate_coverage` sont RÉUTILISÉES par les
    recommandations (les écarts = besoins de formation).

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


def _confiance_ancrage(match: dict) -> float:
    """Confiance d'un ancrage au graphe : rerank_score (cross-encoder ∈[0,1]) si
    présent, sinon le score de proximité embeddings."""
    return float(match.get("rerank_score", match.get("score", 0.0)) or 0.0)


def build_exigences(extraction: dict, min_ancrage: float = 0.0) -> list[dict]:
    """Transforme la sortie d'extraction en liste d'exigences ancrées au graphe.
    Chaque exigence : {competence (libellé canonique), requete (phrase brute),
    importance, skill_id, skill_type}.

    `min_ancrage` (GATE de confiance) : si le meilleur match a une confiance sous
    ce seuil, on le REJETTE (ancrage jugé peu fiable) et on garde le libellé BRUT
    extrait — évite qu'un libellé vague s'ancre sur une compétence hors-sujet
    (« Analyse situation » → « évaluer l'état de navires »). Défaut 0.0 = pas de
    gate (rétrocompat) ; la reco l'active."""
    exigences = []
    for s in extraction.get("skills", []):
        match = s["matches"][0] if s.get("matches") else None
        if match is not None and _confiance_ancrage(match) < min_ancrage:
            match = None   # ancrage trop faible -> on retombe sur le libellé brut, fidèle
        exigences.append({
            "competence": (match["label_fr"] if match else s["raw"]),
            "requete": s["raw"] or (match["label_fr"] if match else ""),
            "importance": s.get("importance") or "essentielle",
            "skill_id": (match["skill_id"] if match else None),
            "skill_type": (match["skill_type"] if match else None),
        })
    return exigences


def evaluate_coverage(profil: list[str], exigences: list[dict], seuil: float = 0.5):
    """Évalue la couverture des exigences par le profil (reranker).
    Renvoie (score, couvertes, ecarts). On teste deux formulations de l'exigence
    (libellé canonique + phrase brute) et on garde la meilleure couverture."""
    profil = [c.strip() for c in profil if c and c.strip()]
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
        base = {"competence": ex["competence"], "importance": ex["importance"],
                "skill_id": ex.get("skill_id"), "skill_type": ex.get("skill_type")}
        if best >= seuil and i_best >= 0:
            couvertes.append({**base, "couverte_par": profil[i_best], "similarite": round(best, 2)})
        else:
            ecarts.append({**base, "meilleure_similarite": round(best, 2)})

    total = sum(_poids(e["importance"]) for e in exigences) or 1.0
    acquis = sum(_poids(c["importance"]) for c in couvertes)
    return round(100 * acquis / total), couvertes, ecarts


def match_profile_to_job(db: Session, profil_competences: list[str],
                         poste_texte: str, seuil: float = 0.5) -> dict:
    """Calcule la correspondance profil ↔ poste (conforme à MatchResponse)."""
    extraction = skill_extraction_service.extract_skills(db, poste_texte, top_k=1)
    exigences = build_exigences(extraction)
    score, couvertes, ecarts = evaluate_coverage(profil_competences, exigences, seuil)
    logger.info("Matching : %d exigences, %d couvertes, score %d.", len(exigences), len(couvertes), score)
    return {
        "score": score,
        "competences_requises": len(exigences),
        "model": extraction.get("model", "?"),
        "couvertes": couvertes,
        "ecarts": ecarts,
    }
