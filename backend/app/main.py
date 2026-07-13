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

from fastapi import FastAPI

from app.core.config import settings
from app.controllers import (skill_extraction_controller, skill_matching_controller,
                             recommendation_controller)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

app = FastAPI(
    title="BMCI Gestion des Carrières — API",
    description="Graphe de compétences (ESCO/O*NET/SFIA) + IA locale, 100 % on-premise.",
    version="0.1.0",
)

# Un routeur par fonctionnalité (MVC : contrôleurs séparés).
app.include_router(skill_extraction_controller.router)
app.include_router(skill_matching_controller.router)
app.include_router(recommendation_controller.router)


@app.get("/sante", tags=["Système"], summary="Vérifier que l'API répond")
def sante() -> dict:
    """Sonde de vivacité — ne dépend ni du LLM ni des embeddings."""
    return {"statut": "ok", "modele_extraction": settings.task_model("extraction_competences").get("model")}
