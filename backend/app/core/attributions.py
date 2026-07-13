#!/usr/bin/env python3
"""
core/attributions.py — Mentions d'attribution EXIGÉES par les fournisseurs de référentiels.

RÔLE
    Source UNIQUE de vérité des mentions légales imposées par ESCO, O*NET et SFIA.
    Ces mentions DOIVENT être affichées sur la plateforme (pied de page + écran
    « Mentions légales & crédits »). Réutilisées par les loaders d'ingestion
    (ReferentialSource.attribution) et, plus tard, par l'API/le frontend.

    ⚠️ Obligation légale : ne pas retirer ces mentions. ESCO (déc. 2011, 2011/833/UE)
    exige la phrase ci-dessous pour tout service intégrant la classification ;
    O*NET (CC BY 4.0) exige l'attribution à l'USDOL/ETA ; SFIA exige le crédit
    à la SFIA Foundation.

EMPLACEMENT MVC
    Couche "core" : constantes transverses.
"""

# Mention imposée par ESCO pour un SERVICE intégrant la classification.
ESCO = "Ce service utilise la classification ESCO de la Commission européenne."

# Mention imposée par O*NET (Creative Commons BY 4.0, USDOL/ETA).
ONET = (
    "Ce service incorpore des informations de O*NET® du U.S. Department of Labor, "
    "Employment and Training Administration (USDOL/ETA). O*NET® est une marque "
    "déposée de l'USDOL/ETA."
)

# Mention pour SFIA (Skills Framework for the Information Age, SFIA Foundation).
SFIA = (
    "Ce service utilise le référentiel SFIA (Skills Framework for the Information Age) "
    "de la SFIA Foundation."
)

# Accès par code de référentiel (aligné sur models.referential.SourceCode).
BY_SOURCE = {"ESCO": ESCO, "ONET": ONET, "SFIA": SFIA}


def for_source(code: str) -> str | None:
    """Renvoie la mention d'attribution requise pour un code de référentiel."""
    return BY_SOURCE.get((code or "").upper())


def all_required() -> list[str]:
    """Liste des mentions à afficher (pied de page / crédits). Ordre stable."""
    return [ESCO, ONET, SFIA]
