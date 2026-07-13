#!/usr/bin/env python3
"""
services/embedding_service.py — Embeddings locaux (Ollama bge-m3).

RÔLE
    Transforme un texte en vecteur (embedding) via bge-m3 servi par Ollama.
    Ces vecteurs alimentent le graphe de compétences et le matching sémantique
    (stockés dans SQLite via sqlite-vec). UNIQUE point d'appel à l'API embeddings.

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

_EMBED_TIMEOUT = 60  # bge-m3 léger ; le 1er appel (chargement modèle) peut être plus long.


def embed_text(text: str) -> list[float]:
    """Renvoie l'embedding d'un texte. Vérifie la dimension pour détecter au plus
    tôt une incohérence de modèle (évite de corrompre la table vectorielle)."""
    if not text or not text.strip():
        raise ValueError("embed_text: texte vide")
    try:
        r = requests.post(
            settings.OLLAMA_EMBED_URL,
            json={"model": settings.OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=_EMBED_TIMEOUT,
        )
        r.raise_for_status()
        vector = r.json().get("embedding")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Ollama n'est pas démarré (lancez 'ollama serve').")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Le modèle d'embedding met trop de temps à répondre.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur d'embedding Ollama: %s", e)
        raise HTTPException(status_code=500, detail="Erreur interne lors de la génération de l'embedding.")

    if not vector or not isinstance(vector, list):
        raise HTTPException(status_code=500, detail="Réponse d'embedding invalide.")
    if len(vector) != settings.EMBED_DIM:
        logger.error("Dimension d'embedding %d (attendu %d) — mauvais modèle ?", len(vector), settings.EMBED_DIM)
        raise HTTPException(status_code=500, detail="Dimension d'embedding incohérente avec la configuration.")
    return vector


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embedde une liste de textes (séquentiel — Ollama sert un texte à la fois)."""
    return [embed_text(t) for t in texts]
