#!/usr/bin/env python3
"""
services/audit_service.py — Journalisation des évènements sensibles.

RÔLE
    Point d'entrée UNIQUE pour tracer un évènement dans `audit_logs`. Best-effort :
    un échec de journalisation ne casse jamais la requête métier. Ouvre sa propre
    session (utilisable depuis n'importe quel contexte). Ne journalise JAMAIS un
    token en clair (on n'en stocke pas la valeur).

EMPLACEMENT MVC
    Couche "services" : traçabilité transverse.
"""

import logging

from app.database.session import SessionLocal
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_event(event_type: str, description: str, *, status: str = "SUCCESS",
              user_id: int | None = None, username: str | None = None,
              role: str | None = None, ip_address: str | None = None,
              user_agent: str | None = None, endpoint: str | None = None,
              http_method: str | None = None) -> None:
    """Enregistre un évènement d'audit (best-effort — n'interrompt jamais l'appelant)."""
    try:
        db = SessionLocal()
        try:
            db.add(AuditLog(
                event_type=event_type, description=description[:2000], status=status,
                user_id=user_id, username=username, role=role, ip_address=ip_address,
                user_agent=(user_agent or "")[:300] or None, endpoint=endpoint,
                http_method=http_method,
            ))
            db.commit()
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 — l'audit ne doit jamais faire échouer la requête
        logger.warning("Audit non enregistré (%s) : %s", event_type, e)
