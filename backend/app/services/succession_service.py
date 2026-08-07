#!/usr/bin/env python3
"""
services/succession_service.py — Plan de succession (tâche IA `raisonnement_batch`).

RÔLE
    Active la tâche `raisonnement_batch` (routing.yaml → qwen3.6, modèle de
    RAISONNEMENT lourd). À partir de la cartographie RÉELLE d'un pôle (collaborateurs,
    postes, compétences+niveaux, aspirations), produit un plan de succession raisonné :
    successeurs internes potentiels, préparation, écarts à combler, postes à risque.
    Tâche BATCH par nature (modèle 23 Go → lent sur 8 Go VRAM) : usage RH ponctuel.

SÉCURITÉ
    100 % local. La cartographie du pôle est fencée comme DONNÉE (anti-injection).

EMPLACEMENT MVC
    Couche "services" : orchestration IA + graphe, sans route HTTP.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import Profil, ProfilCompetence

logger = logging.getLogger(__name__)

# --- Paramètres du calcul de succession ---
_NIVEAU_CLE = 2      # poste « clé » = encadrement (Responsable/Directeur…)
_SEUIL_SUCC = 40     # adéquation minimale (%) pour être un successeur viable
_SEUIL_PRET = 70     # ≥ : prêt maintenant
_SEUIL_MOYEN = 55    # ≥ : prêt à 12-24 mois ; sinon à développer

_MOTS_NIVEAU = (
    (3, ("directeur", "directrice", "chief", "dga", "dg ", "head of")),
    (2, ("responsable", "manager", "chef", "lead", "head", "adjoint")),
    (1, ("senior", "confirmé", "référent", "expert", "principal")),
)


def _niveau_poste(titre: str) -> int:
    """Niveau hiérarchique heuristique d'un intitulé (0 IC → 3 direction)."""
    t = (titre or "").lower()
    for niv, mots in _MOTS_NIVEAU:
        if any(m in t for m in mots):
            return niv
    return 0


def _cap(s: str) -> str:
    s = (s or "").strip()
    return (s[:1].upper() + s[1:]) if s else s


def _readiness(score: int) -> str:
    if score >= _SEUIL_PRET:
        return "Prêt"
    if score >= _SEUIL_MOYEN:
        return "12-24 mois"
    return "À développer"


def _competences_par_profil(db: Session, profil_ids: list[int]) -> dict[int, dict[str, int]]:
    """Map profil_id -> {libellé normalisé: meilleur niveau} (une requête, sans N+1)."""
    comps: dict[int, dict[str, int]] = {}
    if not profil_ids:
        return comps
    for pid, lib, niv in db.execute(
            select(ProfilCompetence.profil_id, ProfilCompetence.libelle, ProfilCompetence.niveau)
            .where(ProfilCompetence.profil_id.in_(profil_ids))).all():
        key = (lib or "").strip().lower()
        if not key:
            continue
        cur = comps.setdefault(pid, {})
        cur[key] = max(cur.get(key, 0), niv or 0)
    return comps


def _nom(p: Profil) -> str:
    return f"{(p.prenom or '').strip()} {p.nom}".strip() or (p.nom or "—")


def plan_succession(db: Session, departement_key: str) -> dict:
    """Plan de succession CALCULÉ (déterministe, rapide) : pour chaque poste
    d'ENCADREMENT du pôle, on classe les successeurs internes par adéquation de
    compétences (recouvrement pondéré par niveau au poste du titulaire) et on en
    déduit la préparation, les écarts à combler et les postes clés À RISQUE."""
    profils = list(db.scalars(
        select(Profil).where(Profil.departement_key == departement_key)
        .order_by(Profil.nom)).all())
    effectif = len(profils)
    comps = _competences_par_profil(db, [p.id for p in profils])
    label = {}
    for cmap in comps.values():
        for lib in cmap:
            label.setdefault(lib, _cap(lib))

    key_holders = [p for p in profils if _niveau_poste(p.poste_actuel or "") >= _NIVEAU_CLE]
    roles = []
    for h in key_holders:
        req = comps.get(h.id) or {}
        total = sum(req.values()) or 1
        cands = []
        for c in profils:
            if c.id == h.id:
                continue
            cc = comps.get(c.id) or {}
            couvert = 0
            manques = []
            for lib, niv_h in req.items():
                niv_c = cc.get(lib, 0)
                couvert += min(niv_c, niv_h)
                if niv_c < niv_h:
                    manques.append((niv_h - niv_c, lib))
            score = round(100 * couvert / total)
            ecarts = [label.get(lib, _cap(lib)) for _, lib in sorted(manques, reverse=True)[:3]]
            cands.append((score, c, ecarts))
        cands.sort(key=lambda x: x[0], reverse=True)
        successeurs = []
        for score, c, ecarts in cands:
            if score < _SEUIL_SUCC or len(successeurs) >= 3:
                break
            successeurs.append({"nom": _nom(c), "poste": c.poste_actuel, "score": score,
                                "readiness": _readiness(score), "ecarts": ecarts})
        roles.append({"poste": h.poste_actuel or "Poste d'encadrement", "titulaire": _nom(h),
                      "successeurs": successeurs, "risque": not successeurs})

    # Postes À RISQUE d'abord (attention RH), puis par relève décroissante.
    roles.sort(key=lambda r: (not r["risque"], -len(r["successeurs"])))
    a_risque = sum(1 for r in roles if r["risque"])
    couverts = len(roles) - a_risque
    if roles:
        synthese = (f"{len(roles)} poste(s) d'encadrement analysé(s) : {couverts} avec une relève "
                    f"interne identifiée, {a_risque} à risque (aucun successeur suffisamment prêt).")
    else:
        synthese = "Aucun poste d'encadrement identifié dans ce pôle."
    return {"departement_key": departement_key, "effectif": effectif,
            "postes_cles": len(roles), "couverts": couverts, "a_risque": a_risque,
            "roles": roles, "synthese": synthese, "plan": synthese,
            "model": "calcul déterministe"}


# --- Version ASYNCHRONE : qwen3.6 (~4 min) ne doit pas tenir une requête HTTP ni
#     bloquer le verrou GPU pendant l'attente du client → thread de fond + polling.
def launch_succession_job(user_id: int, departement_key: str) -> str:
    """Lance le plan de succession en tâche de fond ; renvoie un job_id à interroger."""
    from app.services import async_job
    return async_job.submit(
        user_id, lambda db: plan_succession(db, departement_key), label="succession")


def get_succession_job(job_id: str, user_id: int) -> dict | None:
    """État du job de succession (réservé à son propriétaire). None si inconnu/autre user."""
    from app.services import async_job
    return async_job.get(job_id, user_id)
