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
