#!/usr/bin/env python3
"""
controllers/auth_controller.py — Routes d'authentification.

RÔLE
    Expose /api/auth : connexion (pose les cookies HttpOnly + CSRF), déconnexion
    (révoque la session), et /me (utilisateur courant). Aucune logique métier :
    délègue à auth_service ; l'audit est tracé au passage.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP.
"""

from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_token
from app.database.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, UserPublic, AnnuairePreloadOut
from app.models.user import User
from app.models.audit_log import AuditEventType
from app.services import auth_service, audit_service
from app.auth.dependencies import get_current_user, client_ip, extract_token

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    max_age = settings.TOKEN_EXPIRY_HOURS * 3600
    # Session : HttpOnly (le JS n'y accède jamais).
    response.set_cookie(settings.SESSION_COOKIE, session_token, max_age=max_age, path="/",
                        httponly=True, secure=settings.cookie_secure, samesite=settings.COOKIE_SAMESITE)
    # CSRF : lisible par le JS (double-submit) — renvoyé dans l'en-tête X-CSRF-Token.
    response.set_cookie(settings.CSRF_COOKIE, csrf_token, max_age=max_age, path="/",
                        httponly=False, secure=settings.cookie_secure, samesite=settings.COOKIE_SAMESITE)


@router.post("/login", response_model=LoginResponse, summary="Connexion (auth locale)")
def login(req: LoginRequest, request: Request, response: Response,
          db: Session = Depends(get_db)) -> LoginResponse:
    ip, ua = client_ip(request), request.headers.get("user-agent")
    try:
        user = auth_service.authenticate(db, req.email, req.password, ip=ip, ua=ua)
    except auth_service.AuthError as e:
        raise HTTPException(status_code=(429 if e.code == "locked" else 401), detail=e.message)

    token = auth_service.create_session(db, user, ip=ip, ua=ua)
    csrf = generate_token()
    _set_auth_cookies(response, token, csrf)
    return {"utilisateur": user.to_public(), "csrf_token": csrf}


@router.post("/logout", summary="Déconnexion (révoque la session)")
def logout(request: Request, response: Response, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> dict:
    auth_service.revoke_token(db, extract_token(request))
    audit_service.log_event(AuditEventType.LOGOUT, f"Déconnexion : {user.email}",
                            user_id=user.id, username=user.email, role=user.role)
    response.delete_cookie(settings.SESSION_COOKIE, path="/")
    response.delete_cookie(settings.CSRF_COOKIE, path="/")
    return {"statut": "déconnecté"}


@router.get("/me", response_model=UserPublic, summary="Utilisateur courant")
def me(user: User = Depends(get_current_user)) -> UserPublic:
    return user.to_public()


@router.get("/annuaire-preload", response_model=AnnuairePreloadOut,
            summary="Enrôlement : infos RH pré-existantes par e-mail (démo, pré-auth)")
def annuaire_preload(email: str = Query(..., min_length=3, max_length=255),
                     db: Session = Depends(get_db)) -> AnnuairePreloadOut:
    """Les collaborateurs BMCI existent DÉJÀ en base. À partir de l'e-mail, renvoie
    les infos d'annuaire déjà connues (poste, département, manager) : l'inscription
    ACTIVE le compte et pré-remplit ces champs plutôt que de les ressaisir. Données
    synthétiques de démo (annuaire interne)."""
    return AnnuairePreloadOut(**auth_service.annuaire_preload(db, email))
