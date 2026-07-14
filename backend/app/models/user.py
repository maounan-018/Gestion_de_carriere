#!/usr/bin/env python3
"""
models/user.py — Comptes utilisateurs + sessions.

RÔLE
    `User` = compte (humain réel, de service, ou synthétique de démo) avec son RÔLE
    (RBAC) et son type (répertoire des comptes). `UserSession` = session active
    (token HACHÉ en base, jamais en clair). Fondation de l'authentification et du
    cloisonnement par périmètre.

SÉCURITÉ
    - Mot de passe : jamais stocké en clair (PBKDF2, cf. core/security).
    - Token de session : stocké HACHÉ (SHA-256) — une fuite n'expose aucun token.
    - Pas d'inscription publique (comptes provisionnés par l'admin ou le SSO/JIT).

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Role:
    """Rôles RBAC (périmètre d'accès)."""
    COLLAB = "COLLAB"     # collaborateur : ses propres données
    MANAGER = "MANAGER"   # manager : lui + son équipe
    RH = "RH"            # RH : vue globale, cartographie, offres
    ADMIN = "ADMIN"      # administration (réservé)
    SERVICE = "SERVICE"   # compte technique (connecteurs SIRH/LMS) — non-humain
    ALL = {COLLAB, MANAGER, RH, ADMIN, SERVICE}


class UserType:
    """Nature du compte (répertoire des comptes)."""
    REAL = "real"          # employé réel (SSO/JIT ou provisionné)
    SERVICE = "service"    # compte technique (machine-à-machine)
    SYNTHETIC = "synthetic"  # persona de démo (jamais en production)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(16), default=Role.COLLAB, index=True)
    type: Mapped[str] = mapped_column(String(12), default=UserType.REAL, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), default=None)  # None = SSO/service
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    departement_key: Mapped[str | None] = mapped_column(String(48), default=None)
    matricule: Mapped[str | None] = mapped_column(String(32), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))

    def to_public(self) -> dict:
        """Projection publique (jamais le hash)."""
        return {"id": self.id, "email": self.email, "name": self.name,
                "role": self.role, "type": self.type, "manager_id": self.manager_id,
                "departement_key": self.departement_key}


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # SHA-256
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_session_user", "user_id"),)
