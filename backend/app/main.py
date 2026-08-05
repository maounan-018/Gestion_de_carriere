#!/usr/bin/env python3
"""
main.py — Point d'entrée de l'API BMCI Gestion des Carrières.

RÔLE
    Assemble l'application FastAPI : métadonnées, santé, et enregistrement des
    contrôleurs (un routeur par fonctionnalité). Aucune logique métier ici — tout
    vit dans les couches services/models. Lancer :  uvicorn app.main:app --reload

EMPLACEMENT MVC
    Racine applicative : câblage des couches.
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.http_hardening import SecurityHeadersMiddleware
from app.services import ai_router
from app.controllers import (skill_extraction_controller, skill_matching_controller,
                             recommendation_controller, fiche_controller, auth_controller,
                             profil_controller, offre_controller, candidature_controller,
                             notification_controller, souhait_controller, formation_controller,
                             dashboard_controller, rh_controller, coach_controller,
                             redaction_controller, normalisation_controller,
                             entretien_controller)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Démarrage : précharge les modèles IA en tâche de fond (ne bloque ni le boot
    ni la matérialisation des routes). Best-effort — ignoré si Ollama est éteint."""
    if settings.AI_WARMUP_MODELS:
        threading.Thread(target=ai_router.warmup, name="ollama-warmup", daemon=True).start()
    yield


app = FastAPI(
    title="BMCI Gestion des Carrières — API",
    description="Graphe de compétences (ESCO/O*NET/SFIA) + IA locale, 100 % on-premise.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — origines explicites + credentials (cookies). JAMAIS "*" avec credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", settings.CSRF_HEADER],
)

# Compression GZip des réponses (listes offres/candidatures, cartographie, synthèse
# RH…). N'agit que sur les réponses > 1 Ko qui acceptent gzip ; gère aussi le
# streaming (SSE non compressé car petits événements). Gain bande passante/latence.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Durcissement HTTP — ajouté APRÈS le CORS => couche la PLUS EXTERNE (Starlette
# applique les middlewares dans l'ordre inverse d'ajout) : en-têtes de sécurité
# sur chaque réponse + rejet des corps trop volumineux (413).
app.add_middleware(SecurityHeadersMiddleware)

# Un routeur par fonctionnalité (MVC : contrôleurs séparés).
app.include_router(auth_controller.router)
app.include_router(skill_extraction_controller.router)
app.include_router(skill_matching_controller.router)
app.include_router(recommendation_controller.router)
app.include_router(fiche_controller.router)
app.include_router(profil_controller.router)
app.include_router(offre_controller.router)
app.include_router(candidature_controller.router)
app.include_router(notification_controller.router)
app.include_router(souhait_controller.router)
app.include_router(formation_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(rh_controller.router)
app.include_router(coach_controller.router)
app.include_router(redaction_controller.router)
app.include_router(normalisation_controller.router)
app.include_router(entretien_controller.router)


@app.get("/sante", tags=["Système"], summary="Vérifier que l'API répond")
def sante() -> dict:
    """Sonde de vivacité — ne dépend ni du LLM ni des embeddings."""
    return {"statut": "ok", "modele_extraction": settings.task_model("extraction_competences").get("model")}
