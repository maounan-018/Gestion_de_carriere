#!/usr/bin/env python3
"""
services/auth_service.py — Authentification & sessions.

RÔLE
    Cœur de l'authentification (repris de smart-objective, adapté aux rôles et types
    de comptes BMCI) :
      - `authenticate` : vérifie les identifiants (auth locale), avec anti-brute-force
        (verrouillage après N échecs récents, comptés dans l'audit) ;
      - `create_session` : émet un token de session (stocké HACHÉ en base) ;
      - `resolve_token` : retrouve l'utilisateur depuis un token (cookie/Bearer),
        vérifie l'expiration et l'activation du compte ;
      - `revoke_token` : invalide une session (déconnexion).
    Le SSO SAML se branchera plus tard via un provider d'identité (JIT provisioning) ;
    ici on couvre l'auth locale (comptes provisionnés / personas de démo).

SÉCURITÉ
    Mots de passe PBKDF2 ; tokens hachés en base ; aucun token en clair journalisé ;
    comptes SERVICE non autorisés à la connexion par mot de passe.

EMPLACEMENT MVC
    Couche "services" : logique d'authentification, sans route HTTP.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, generate_token, hash_token
from app.models.user import User, UserSession, UserType
from app.models.audit_log import AuditLog, AuditEventType
from app.services import audit_service

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Erreur d'authentification métier (code : 'invalid' | 'locked' | 'inactive')."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _recent_failures(db: Session, email: str) -> int:
    """Nombre d'échecs de connexion récents (fenêtre de verrouillage) pour cet e-mail."""
    since = datetime.now(timezone.utc) - timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
    return db.scalar(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.event_type == AuditEventType.LOGIN_FAILED,
            AuditLog.username == email,
            AuditLog.created_at >= since,
        )
    ) or 0


def authenticate(db: Session, email: str, password: str, *,
                 ip: str | None = None, ua: str | None = None) -> User:
    """Vérifie les identifiants (auth locale). Lève AuthError sinon."""
    email = (email or "").strip().lower()

    if _recent_failures(db, email) >= settings.MAX_LOGIN_ATTEMPTS:
        audit_service.log_event(
            AuditEventType.LOGIN_FAILED, f"Compte temporairement verrouillé : {email}",
            status="FAILED", username=email, ip_address=ip, user_agent=ua)
        raise AuthError("locked",
                        f"Trop de tentatives. Réessayez dans {settings.LOGIN_LOCKOUT_MINUTES} minutes.")

    user = db.scalar(select(User).where(User.email == email))
    # Comptes SERVICE : jamais de connexion par mot de passe (machine-à-machine).
    valid = bool(
        user and user.is_active and user.type != UserType.SERVICE
        and user.password_hash and verify_password(password, user.password_hash)
    )
    if not valid:
        audit_service.log_event(
            AuditEventType.LOGIN_FAILED, f"Échec d'authentification : {email}",
            status="FAILED", username=email, ip_address=ip, user_agent=ua)
        raise AuthError("invalid", "Identifiants invalides.")

    return user


def create_session(db: Session, user: User, *,
                   ip: str | None = None, ua: str | None = None) -> str:
    """Crée une session et renvoie le token EN CLAIR (à poser en cookie).
    Seul son hachage est stocké en base."""
    token = generate_token()
    db.add(UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.TOKEN_EXPIRY_HOURS),
    ))
    db.commit()
    audit_service.log_event(
        AuditEventType.LOGIN_SUCCESS, f"Connexion réussie : {user.email}",
        user_id=user.id, username=user.email, role=user.role, ip_address=ip, user_agent=ua)
    return token


def resolve_token(db: Session, token: str | None) -> User | None:
    """Retrouve l'utilisateur d'un token valide (non expiré, compte actif), sinon None.
    Purge la session si expirée."""
    if not token:
        return None
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if not session:
        return None
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        return None
    return user


def revoke_token(db: Session, token: str | None) -> None:
    """Invalide la session associée à ce token (déconnexion)."""
    if not token:
        return
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if session:
        db.delete(session)
        db.commit()
