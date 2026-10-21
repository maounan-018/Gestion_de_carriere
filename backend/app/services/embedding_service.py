#!/usr/bin/env python3
"""
services/embedding_service.py — Embeddings locaux PAR LOTS (Ollama bge-m3, /api/embed).

RÔLE
    Transforme des textes en vecteurs via bge-m3 (Ollama). Utilise l'endpoint
    /api/embed qui accepte une LISTE en entrée -> embeddings par lots (~18 ms/embed
    contre ~2 s en un-par-un : indispensable pour ingérer ESCO ~14k compétences).
    UNIQUE point d'appel à l'API d'embeddings de toute la plateforme.

SÉCURITÉ
    100 % local : aucune donnée ne sort. URL et modèle viennent de la config.

EMPLACEMENT MVC
    Couche "services" : logique métier (embeddings), sans route HTTP.
"""

import logging

import requests
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

_EMBED_TIMEOUT = 180  # un lot de quelques centaines de textes tient largement dedans


class EmbeddingBatchRejected(Exception):
    """Ollama a rejeté le lot (400) — typiquement un lot trop volumineux.
    Signale au niveau supérieur qu'il faut scinder et réessayer."""


def _embed(inputs: list[str]) -> list[list[float]]:
    """Appelle /api/embed sur une liste de textes -> liste de vecteurs.
    Vérifie la dimension pour détecter tôt une incohérence de modèle."""
    if not inputs:
        return []
    # Garde-fou : Ollama /api/embed renvoie 400 sur un texte vide. On remplace tout
    # texte vide/blanc par un placeholder pour garder l'alignement lot<->vecteurs.
    safe_inputs = [t if (t and t.strip()) else "." for t in inputs]
    try:
        r = requests.post(
            settings.OLLAMA_EMBED_URL,
            json={"model": settings.OLLAMA_EMBED_MODEL, "input": safe_inputs},
            timeout=_EMBED_TIMEOUT,
        )
        r.raise_for_status()
        vectors = r.json().get("embeddings")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Ollama n'est pas démarré (lancez 'ollama serve')."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Le modèle d'embedding met trop de temps à répondre."
        )
    except requests.exceptions.HTTPError as e:
        # 400 = lot rejeté (trop volumineux) -> laisser le niveau supérieur scinder.
        raise EmbeddingBatchRejected(str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur d'embedding Ollama: %s", e)
        raise HTTPException(
            status_code=500, detail="Erreur interne lors de la génération de l'embedding."
        )

    if not vectors or not isinstance(vectors, list) or len(vectors) != len(inputs):
        raise HTTPException(status_code=500, detail="Réponse d'embedding invalide.")
    if len(vectors[0]) != settings.EMBED_DIM:
        logger.error(
            "Dimension d'embedding %d (attendu %d) — mauvais modèle ?",
            len(vectors[0]),
            settings.EMBED_DIM,
        )
        raise HTTPException(
            status_code=500, detail="Dimension d'embedding incohérente avec la configuration."
        )
    return vectors


def embed_text(text: str) -> list[float]:
    """Embedding d'un seul texte (recherche/matching à la volée)."""
    if not text or not text.strip():
        raise ValueError("embed_text: texte vide")
    return _embed([text])[0]


def embed_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embedde une liste de textes par lots, avec REPLI ADAPTATIF : si Ollama
    rejette un lot (400 — lot trop volumineux), on le scinde en deux et on
    réessaie récursivement jusqu'à l'unité. L'ingestion ne plante plus jamais
    sur une limite de lot ou un libellé pathologique."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        out.extend(_embed_resilient(texts[i : i + batch_size]))
    return out


def _embed_resilient(chunk: list[str]) -> list[list[float]]:
    """Embedde un lot ; sur rejet, scinde en deux et réessaie récursivement."""
    try:
        return _embed(chunk)
    except EmbeddingBatchRejected:
        if len(chunk) <= 1:
            # Un unique texte rejeté (ultra-rare) : on retente un placeholder
            # connu-bon pour ne pas casser l'ingestion ni l'alignement.
            logger.warning("Texte rejeté isolément, placeholder substitué : %r", chunk[0][:80])
            return _embed(["."])
        mid = len(chunk) // 2
        return _embed_resilient(chunk[:mid]) + _embed_resilient(chunk[mid:])
