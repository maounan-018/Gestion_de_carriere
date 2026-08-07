#!/usr/bin/env python3
"""
schemas/auth.py — Contrats d'authentification.

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic). Jamais de hash exposé.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=256)


class UserPublic(BaseModel):
    id: int
    email: str
    name: str
    role: str
    type: str
    manager_id: int | None = None
    departement_key: str | None = None


class LoginResponse(BaseModel):
    utilisateur: UserPublic
    # Jeton CSRF (double-submit) : le front le renvoie dans l'en-tête X-CSRF-Token
    # sur chaque requête mutante. Aussi posé en cookie NON-HttpOnly.
    csrf_token: str
    # Jeton de session, aussi posé en cookie HttpOnly (chemin same-origin). Renvoyé
    # dans le corps pour l'auth CROSS-ORIGIN par en-tête `Authorization: Bearer`,
    # quand le front (ex. déployé sur Vercel) et le backend (FastAPI local) sont sur
    # des origines différentes : les cookies cross-site ne s'appliquent alors pas.
    token: str


class AnnuairePreloadOut(BaseModel):
    """Pré-remplissage d'enrôlement : infos RH DÉJÀ EN BASE pour un e-mail donné.
    Démo : les collaborateurs BMCI existent déjà ; l'inscription active le compte."""
    found: bool
    nom: str | None = None
    prenom: str | None = None
    poste_actuel: str | None = None
    departement: str | None = None
    manager_nom: str | None = None
