#!/usr/bin/env python3
"""
controllers/normalisation_controller.py — Outil de normalisation d'une saisie libre.

RÔLE
    Expose, en API réutilisable, la « structuration » d'une saisie humaine bruitée
    (fautes, franglais, annotations parasites) en un intitulé canonique + un drapeau
    de confiance. Utilisé en interne par la reco, mais aussi appelable directement
    (objectif de carrière saisi au profil, souhait de mobilité, etc.).

SÉCURITÉ
    `get_current_user` obligatoire + rate-limit IA (l'appel sollicite un LLM local).

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.core.rate_limit import ia_rate_limit
from app.schemas.normalisation import NormaliserCibleRequest, NormaliserCibleResponse
from app.services import input_normalization_service

router = APIRouter(prefix="/api/normalisation", tags=["Normalisation"])


@router.post(
    "/cible",
    response_model=NormaliserCibleResponse,
    dependencies=[Depends(get_current_user), Depends(ia_rate_limit)],
    summary="Structurer une saisie libre en intitulé canonique + confiance",
)
def normaliser_cible(req: NormaliserCibleRequest) -> NormaliserCibleResponse:
    """Nettoie une saisie (fautes, annotations, franglais) en un intitulé de poste
    canonique. `confiance` : 'clair' (intention nette) / 'ambigu' (trop vague, à
    préciser) / 'indisponible' (service IA momentanément indisponible)."""
    return NormaliserCibleResponse(**input_normalization_service.normaliser_cible(req.texte))
