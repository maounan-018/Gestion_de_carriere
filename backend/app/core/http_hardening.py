#!/usr/bin/env python3
"""
core/http_hardening.py — Durcissement HTTP (en-têtes de sécurité + taille de requête).

RÔLE
    Middleware transverse qui (1) rejette les corps de requête trop volumineux
    (413, avant tout traitement) et (2) pose les en-têtes de sécurité sur chaque
    réponse. Complète le rate-limit IA (abus applicatif) sur la surface HTTP :
    clickjacking, sniffing MIME, fuite de referrer, features navigateur, transport.
    100 % local, aucune dépendance externe.

    Implémentation ASGI PURE (pas BaseHTTPMiddleware) : on n'enveloppe pas le corps,
    donc le streaming SSE du Coach (`/api/coach/stream`) n'est pas bufferisé.

    CSP : stricte pour l'API JSON (`default-src 'none'`), NON posée sur la doc
    interactive (/docs, /redoc, /openapi.json) qui charge Swagger UI/ReDoc.
    HSTS : uniquement en production (HTTPS) — inutile en dev HTTP local.

EMPLACEMENT MVC
    Couche "core" : sécurité transverse, sans logique métier.
"""

from __future__ import annotations

from starlette.responses import JSONResponse

from app.core.config import settings

# Doc interactive : la CSP stricte casserait Swagger/ReDoc -> on ne la pose pas là.
_DOC_PREFIXES = ("/docs", "/redoc")
_DOC_PATHS = {"/openapi.json"}

# CSP stricte pour les réponses d'API (JSON) : rien à charger, rien à encadrer.
_API_CSP = b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

# En-têtes posés sur TOUTES les réponses (valeurs en bytes pour l'ASGI).
_BASE_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"geolocation=(), microphone=(), camera=(), browsing-topics=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
]
_HSTS = (b"strict-transport-security", b"max-age=63072000; includeSubDomains")


def _is_doc(path: str) -> bool:
    return path in _DOC_PATHS or path.startswith(_DOC_PREFIXES)


class SecurityHeadersMiddleware:
    """Middleware ASGI : plafond de taille de requête + en-têtes de sécurité."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        skip_csp = _is_doc(path)

        # Private Network Access (Chrome) : un site public/HTTPS (ex. front Vercel)
        # qui appelle une adresse privée/localhost (backend FastAPI local) déclenche
        # un préflight portant `Access-Control-Request-Private-Network: true`. Le
        # backend DOIT répondre `Access-Control-Allow-Private-Network: true` pour que
        # la requête réelle soit autorisée. Le CORSMiddleware ne gère pas cet en-tête.
        wants_pna = any(
            k == b"access-control-request-private-network" and v == b"true"
            for k, v in (scope.get("headers") or [])
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                present = {k.lower() for k, _ in headers}
                for k, v in _BASE_HEADERS:
                    if k not in present:
                        headers.append((k, v))
                if not skip_csp and b"content-security-policy" not in present:
                    headers.append((b"content-security-policy", _API_CSP))
                if settings.is_production and b"strict-transport-security" not in present:
                    headers.append(_HSTS)
                if wants_pna and b"access-control-allow-private-network" not in present:
                    headers.append((b"access-control-allow-private-network", b"true"))
            await send(message)

        # Plafond de taille : Content-Length déclaré > limite -> 413 immédiat.
        for name, value in scope.get("headers") or []:
            if name == b"content-length":
                try:
                    too_big = int(value) > settings.MAX_REQUEST_SIZE_BYTES
                except ValueError:
                    too_big = False
                if too_big:
                    resp = JSONResponse(
                        status_code=413, content={"detail": "Requête trop volumineuse."}
                    )
                    await resp(scope, receive, send_wrapper)
                    return
                break

        await self.app(scope, receive, send_wrapper)
