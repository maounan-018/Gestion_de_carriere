#!/usr/bin/env python3
"""
core/rate_limit.py — Limitation de débit en mémoire pour les endpoints IA.

RÔLE
    Protège les endpoints IA coûteux (Coach, reco, succession, extraction,
    rédaction, matching, génération de fiche) contre l'abus / la saturation.
    Le GPU est SÉRIALISÉ (une seule génération LLM à la fois, VRAM 8 Go — cf.
    `_GPU_LOCK` dans ai_router) : un utilisateur qui enchaîne les requêtes remplit
    la file et prive les autres. On borne, PAR UTILISATEUR :
      - le DÉBIT : N requêtes IA max sur une fenêtre glissante (défaut 15 / 60 s) ;
      - la CONCURRENCE : K requêtes IA en vol simultanées max (défaut 2).
    Dépassement -> HTTP 429 (+ `Retry-After`), journalisé (audit = détection d'abus).

PORTÉE
    Process unique (uvicorn 1 worker) + threads -> stockage MÉMOIRE thread-safe,
    cohérent avec le `threading.Semaphore` du GPU. Pas de Redis (100 % local).
    (Multi-worker un jour -> déplacer l'état vers un store partagé.)

EMPLACEMENT MVC
    Couche "core" : primitive de sécurité transverse, sans logique métier.
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque

from fastapi import Depends, Request, HTTPException

from app.core.config import settings
from app.auth.dependencies import get_current_user, client_ip
from app.models.user import User
from app.models.audit_log import AuditEventType
from app.services import audit_service


class IARateLimiter:
    """Fenêtre glissante + compteur de concurrence, PAR UTILISATEUR (en mémoire).

    `acquire` réserve un créneau (True/retry) ; `release` libère la concurrence à
    la fin de la requête. Thread-safe (un seul verrou : sections critiques courtes)."""

    def __init__(self, max_per_window: int, window_seconds: int, max_concurrent: int):
        self.max_per_window = max_per_window
        self.window = window_seconds
        self.max_concurrent = max_concurrent
        self._hits: dict[int, deque] = defaultdict(deque)   # horodatages récents / user
        self._inflight: dict[int, int] = defaultdict(int)   # requêtes IA en vol / user
        self._lock = threading.Lock()

    def acquire(self, user_id: int) -> tuple[bool, int]:
        """Tente de réserver un créneau IA. Renvoie (autorisé, retry_after_secondes).
        Sur succès, incrémente la concurrence : l'appelant DOIT appeler `release`."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[user_id]
            cutoff = now - self.window
            while hits and hits[0] <= cutoff:      # purge la fenêtre expirée
                hits.popleft()
            if self._inflight[user_id] >= self.max_concurrent:
                return False, 1                    # déjà K requêtes en vol
            if len(hits) >= self.max_per_window:
                retry = max(1, int(self.window - (now - hits[0])) + 1)
                return False, retry                # débit dépassé sur la fenêtre
            hits.append(now)
            self._inflight[user_id] += 1
            return True, 0

    def release(self, user_id: int) -> None:
        """Libère un créneau de concurrence (à la fin de la requête). Best-effort."""
        with self._lock:
            if self._inflight.get(user_id):
                self._inflight[user_id] -= 1
                if self._inflight[user_id] <= 0:
                    self._inflight.pop(user_id, None)

    def reset(self) -> None:
        """Vide tout l'état (fenêtres + concurrence). Utilisé par les tests."""
        with self._lock:
            self._hits.clear()
            self._inflight.clear()


# Limiteur partagé (singleton module), configuré depuis l'environnement.
_limiter = IARateLimiter(
    max_per_window=settings.IA_RATE_MAX_PER_WINDOW,
    window_seconds=settings.IA_RATE_WINDOW_SECONDS,
    max_concurrent=settings.IA_RATE_MAX_CONCURRENT,
)


def ia_rate_limit(request: Request, user: User = Depends(get_current_user)):
    """Dépendance FastAPI : borne le débit IA par utilisateur (429 si dépassement).

    Dépend de `get_current_user` -> l'authentification ET le CSRF sont déjà vérifiés
    (dépendance mise en cache par requête : pas de double résolution). Générateur à
    `yield` : la concurrence est libérée après l'envoi de la réponse (streaming inclus)."""
    if not settings.IA_RATE_LIMIT_ENABLED:
        yield
        return
    ok, retry_after = _limiter.acquire(user.id)
    if not ok:
        audit_service.log_event(
            AuditEventType.RATE_LIMITED,
            f"Débit IA dépassé sur {request.url.path}",
            status="FAILED", user_id=user.id, username=user.email, role=user.role,
            ip_address=client_ip(request), user_agent=request.headers.get("user-agent"),
            endpoint=request.url.path, http_method=request.method)
        raise HTTPException(
            status_code=429,
            detail="Trop de requêtes IA en peu de temps. Réessayez dans un instant.",
            headers={"Retry-After": str(retry_after)})
    try:
        yield
    finally:
        _limiter.release(user.id)
