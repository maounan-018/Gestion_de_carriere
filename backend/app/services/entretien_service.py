#!/usr/bin/env python3
"""
services/entretien_service.py — Synthèse de préparation d'entretien (sortie IA persistée).

RÔLE
    Enregistre / relit la SYNTHÈSE de la simulation de préparation d'entretien du
    collaborateur connecté (une ligne courante par profil, upsert). Source durable :
    la simulation produit un livrable réutilisable, exportable (PDF côté front).

EMPLACEMENT MVC
    Couche "services" : logique métier + persistance.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entretien_synthese import EntretienSynthese
from app.services import profil_service


def enregistrer_ma_synthese(db: Session, user_id: int, synthese: str) -> dict | None:
    """Upsert de la synthèse de préparation d'entretien du profil lié au compte.
    None si le compte n'a pas de profil. La synthèse est une donnée générée utile :
    elle est CONSERVÉE (jamais « live seulement »)."""
    profil_id = profil_service.profil_id_de_user(db, user_id)
    if profil_id is None:
        return None
    row = db.scalar(select(EntretienSynthese).where(EntretienSynthese.profil_id == profil_id))
    if row is None:
        row = EntretienSynthese(profil_id=profil_id, synthese=synthese)
        db.add(row)
    else:
        row.synthese = synthese
    db.commit()
    db.refresh(row)
    return _to_dict(row)


def charger_ma_synthese(db: Session, user_id: int) -> dict | None:
    """Dernière synthèse persistée du profil lié au compte (ou None)."""
    profil_id = profil_service.profil_id_de_user(db, user_id)
    if profil_id is None:
        return None
    row = db.scalar(select(EntretienSynthese).where(EntretienSynthese.profil_id == profil_id))
    return _to_dict(row) if row else None


def _to_dict(row: EntretienSynthese) -> dict:
    return {
        "synthese": row.synthese,
        "enregistre_le": (row.updated_at or row.created_at).isoformat(),
    }
