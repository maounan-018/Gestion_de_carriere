#!/usr/bin/env python3
"""
models/audit_log.py — Journal d'audit (traçabilité des évènements sensibles).

RÔLE
    Enregistre les évènements sensibles (connexions, accès refusés, sessions,
    accès à des profils, matching, exports…) pour l'auditabilité et la détection
    d'abus. Le token n'est JAMAIS journalisé en clair.

EMPLACEMENT MVC
    Couche "models" : entité ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditEventType:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    ACCESS_DENIED = "ACCESS_DENIED"       # 401/403 (token/CSRF/rôle)
    SESSION_EXPIRED = "SESSION_EXPIRED"
    USER_CREATED = "USER_CREATED"
    SENSITIVE_READ = "SENSITIVE_READ"      # accès à un profil / données RH
    EXPORT = "EXPORT"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="SUCCESS")  # SUCCESS | FAILED
    user_id: Mapped[int | None] = mapped_column(Integer, default=None, index=True)
    username: Mapped[str | None] = mapped_column(String(255), default=None)
    role: Mapped[str | None] = mapped_column(String(16), default=None)
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(300), default=None)
    endpoint: Mapped[str | None] = mapped_column(String(200), default=None)
    http_method: Mapped[str | None] = mapped_column(String(8), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True)
