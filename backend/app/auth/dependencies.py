#!/usr/bin/env python3
"""
auth/dependencies.py — Dépendances d'authentification & guards RBAC.

RÔLE
    Fournit les dépendances FastAPI qui protègent les routes :
      - `get_current_user` : résout l'utilisateur (cookie HttpOnly OU Bearer),
        et vérifie le CSRF (double-submit) sur les méthodes mutantes ;
      - `require_roles(*roles)` : restreint une route à certains rôles (RBAC) ;
      - helpers `client_ip` / `extract_token`.
    Toute route sensible dépend de ces guards → cloisonnement par périmètre.

SÉCURITÉ
    CSRF double-submit : le cookie CSRF (non-HttpOnly) doit égaler l'en-tête
    X-CSRF-Token sur POST/PUT/PATCH/DELETE. Accès refusés journalisés (audit).

EMPLACEMENT MVC
    Couche "auth" : sécurité transverse (dépendances), sans logique métier.
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.models.audit_log import AuditEventType
from app.services import auth_service, audit_service

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def extract_token(request: Request) -> str | None:
    """Token de session : cookie HttpOnly en priorité, sinon en-tête Authorization Bearer."""
    cookie = request.cookies.get(settings.SESSION_COOKIE)
    if cookie:
        return cookie
    authz = request.headers.get("Authorization", "")
    if authz.lower().startswith("bearer "):
        return authz[7:].strip()
    return None


def _check_csrf(request: Request) -> None:
    if request.method in _SAFE_METHODS:
        return
    cookie = request.cookies.get(settings.CSRF_COOKIE)
    header = request.headers.get(settings.CSRF_HEADER)
    if not cookie or not header or cookie != header:
        raise HTTPException(status_code=403, detail="Jeton CSRF manquant ou invalide.")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Exige un utilisateur authentifié (+ CSRF sur les méthodes mutantes)."""
    _check_csrf(request)
    user = auth_service.resolve_token(db, extract_token(request))
    if not user:
        audit_service.log_event(
            AuditEventType.ACCESS_DENIED, f"Accès non authentifié : {request.url.path}",
            status="FAILED", ip_address=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            endpoint=request.url.path, http_method=request.method)
        raise HTTPException(status_code=401, detail="Authentification requise.")
    return user


def require_roles(*roles: str):
    """Fabrique un guard RBAC restreignant la route aux rôles indiqués."""
    def guard(request: Request, user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            audit_service.log_event(
                AuditEventType.ACCESS_DENIED,
                f"Rôle insuffisant ({user.role}) pour {request.url.path}",
                status="FAILED", user_id=user.id, username=user.email, role=user.role,
                endpoint=request.url.path, http_method=request.method)
            raise HTTPException(status_code=403, detail="Droits insuffisants.")
        return user
    return guard
