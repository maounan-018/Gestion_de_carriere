#!/usr/bin/env python3
"""
core/security.py — Primitives de sécurité (hachage de mots de passe, tokens).

RÔLE
    Source de vérité unique des opérations cryptographiques :
      - hachage des mots de passe (PBKDF2-HMAC-SHA256, salé) ;
      - vérification à temps constant ;
      - génération + hachage des tokens de session (stockés hachés en base).

POURQUOI PBKDF2
    SHA-256 simple sans sel est vulnérable (rainbow tables, brute-force GPU).
    PBKDF2 = sel aléatoire par utilisateur + coût de calcul élevé (itérations).

EMPLACEMENT MVC
    Couche "core" : sécurité transverse, réutilisée par les services.
"""

import hashlib
import hmac
import secrets

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hache un mot de passe avec PBKDF2-HMAC-SHA256 + sel aléatoire."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, settings.PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${settings.PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie un mot de passe à temps constant (comparaison anti-timing)."""
    if not stored_hash:
        return False
    try:
        algo, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def generate_token() -> str:
    """Token de session cryptographiquement sûr (256 bits)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash non réversible d'un token (stockage en base). Le token étant déjà à
    haute entropie, un SHA-256 suffit : une fuite de la table sessions n'expose
    aucun token réutilisable."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
