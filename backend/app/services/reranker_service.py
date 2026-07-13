#!/usr/bin/env python3
"""
services/reranker_service.py — Reranking sémantique (bge-reranker-v2-m3, transformers).

RÔLE
    Reclasse un petit ensemble de candidats (issus de la recherche vectorielle) par
    PERTINENCE réelle vis-à-vis d'une requête, via un cross-encoder multilingue. Là
    où l'embedding seul confond des libellés proches en surface (« analyse
    incidents » ↔ « analyser des traces de sang »), le reranker tranche.
    Modèle piloté directement via transformers (AutoModelForSequenceClassification)
    — chemin canonique de bge-reranker, robuste et sans dépendance fragile.
    Chargé paresseusement (modèle lourd) et une seule fois (singleton thread-safe).

SÉCURITÉ
    100 % local (modèle en cache Hugging Face, CPU). Aucune donnée ne sort.

EMPLACEMENT MVC
    Couche "services" : logique IA (reranking), sans route HTTP.
"""

import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None
_lock = threading.Lock()


def _load():
    """Charge (une fois) le cross-encoder bge-reranker-v2-m3 sur CPU."""
    global _tokenizer, _model
    if _model is None:
        with _lock:
            if _model is None:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                logger.info("Chargement du reranker %s (CPU, cache local)…", settings.RERANKER_MODEL)
                # local_files_only : jamais d'appel réseau (modèle en cache HF) —
                # robuste ET conforme à l'exigence 100 % local.
                _tokenizer = AutoTokenizer.from_pretrained(
                    settings.RERANKER_MODEL, local_files_only=True)
                _model = AutoModelForSequenceClassification.from_pretrained(
                    settings.RERANKER_MODEL, local_files_only=True
                ).eval()
    return _tokenizer, _model


def rerank_scores(query: str, passages: list[str], max_length: int = 512) -> list[float]:
    """Renvoie un score de pertinence ∈ [0,1] (sigmoïde du logit) pour chaque
    passage, dans l'ordre d'entrée. Liste vide -> liste vide."""
    if not query or not passages:
        return []
    import torch

    tokenizer, model = _load()
    pairs = [[query, p or ""] for p in passages]
    with torch.no_grad():
        inputs = tokenizer(
            pairs, padding=True, truncation=True,
            max_length=max_length, return_tensors="pt",
        )
        logits = model(**inputs).logits.view(-1).float()
        scores = torch.sigmoid(logits)
    return [float(s) for s in scores]
