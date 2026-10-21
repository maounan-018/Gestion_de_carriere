#!/usr/bin/env python3
"""
services/async_job.py — Petit registre de jobs asynchrones EN MÉMOIRE.

RÔLE
    Factorise le motif « tâche IA LENTE → on ne tient pas la requête HTTP → thread
    de fond (session DB dédiée) + polling par job_id » déjà éprouvé sur la reco.
    Une tâche coûteuse (ex. plan de succession qwen3.6 ~4 min) ne doit pas bloquer
    une requête HTTP (timeout proxy) ni tenir le verrou GPU pendant que le client
    attend : on la lance en tâche de fond et le client interroge un job_id.

SÉCURITÉ
    Chaque job est RÉSERVÉ à son propriétaire (user_id) : `get` renvoie None pour
    un autre utilisateur. Store PROCESS-LOCAL (démo mono-worker) — en multi-worker
    il faudrait un backend partagé (Redis/DB).

EMPLACEMENT MVC
    Couche "services" : utilitaire d'orchestration, sans route HTTP.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_JOB_TTL_S = 900  # 15 min de rétention d'un job terminé (le temps du polling)
_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def _prune(now: float) -> None:
    """Purge les jobs plus vieux que le TTL (évite la fuite mémoire du store)."""
    for k in [k for k, j in _jobs.items() if now - j["created_at"] > _JOB_TTL_S]:
        _jobs.pop(k, None)


def submit(user_id: int, work: Callable[[Session], Any], *, label: str = "job") -> str:
    """Lance `work(db)` en tâche de fond (session DB DÉDIÉE) et renvoie un job_id.

    `work` reçoit une Session SQLAlchemy et renvoie un résultat sérialisable
    (dict). Les erreurs sont capturées → statut `error`. La session est fermée
    dans tous les cas."""
    job_id = uuid.uuid4().hex
    now = time.time()
    with _lock:
        _prune(now)
        _jobs[job_id] = {
            "status": "pending",
            "user_id": user_id,
            "result": None,
            "error": None,
            "created_at": now,
        }

    def _run() -> None:
        from app.database.session import SessionLocal

        db = SessionLocal()
        try:
            res = work(db)
            with _lock:
                if job_id in _jobs:
                    _jobs[job_id].update(status="done", result=res)
        except Exception as e:
            logger.warning("Job %s (%s) échoué : %s", job_id[:8], label, e)
            with _lock:
                if job_id in _jobs:
                    _jobs[job_id].update(status="error", error=str(e))
        finally:
            db.close()

    threading.Thread(target=_run, name=f"{label}-{job_id[:8]}", daemon=True).start()
    return job_id


def get(job_id: str, user_id: int) -> dict | None:
    """État d'un job (RÉSERVÉ à son propriétaire) : {status, result, error}.
    None si le job est inconnu ou appartient à un autre utilisateur."""
    with _lock:
        j = _jobs.get(job_id)
        if not j or j["user_id"] != user_id:
            return None
        return {"status": j["status"], "result": j["result"], "error": j["error"]}
