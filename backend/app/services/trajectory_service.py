#!/usr/bin/env python3
"""
services/trajectory_service.py — Inférence de FAISABILITÉ d'aspiration.

RÔLE
    À partir des PARCOURS observés dans la population (le « CV » structuré de
    chacun : ProfilStation), estime si l'aspiration d'un collaborateur (poste visé)
    est atteignable, et si la trajectoire serait LINÉAIRE ou NON LINÉAIRE — avec une
    explication et des étapes intermédiaires typiques. Heuristique déterministe,
    SANS LLM : on s'appuie sur les collègues ayant déjà atteint un poste comparable
    et sur les rungs par lesquels ils sont passés.

EMPLACEMENT MVC
    Couche "services" : logique métier (lecture seule).
"""

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import Profil
from app.models.carriere import ProfilStation, StationEtat

_STOP = {"de", "du", "des", "la", "le", "les", "et", "en", "un", "une", "au", "aux",
         "sur", "pour", "par", "avec",
         # mots de NIVEAU (pas de domaine) : exclus du rapprochement pour matcher la
         # FILIÈRE (risques, patrimoine, corporate…), pas le grade.
         "directeur", "directrice", "rice", "responsable", "adjoint", "adjointe",
         "senior", "junior", "chef", "cheffe"}


def _niveau(titre: str) -> int:
    """Niveau hiérarchique heuristique (0 IC junior → 3 direction)."""
    t = (titre or "").lower()
    if "directeur" in t or "directrice" in t:
        return 3
    if t.startswith("responsable") or "responsable " in t:
        return 2
    if any(k in t for k in ("senior", "expert", "spécialiste", "architecte",
                            "lead", "chef de mission", "principal")):
        return 1
    return 0


def _tokens(s: str) -> set[str]:
    return {w for w in re.split(r"[^a-zàâäéèêëïîôöùûüç]+", (s or "").lower())
            if len(w) > 2 and w not in _STOP}


def _similar(a: str, b: str) -> float:
    """Recouvrement de tokens de `a` (aspiration) couvert par `b` (poste candidat)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta)


def _humaniser(key: str | None) -> str:
    return key.replace("_", " ").title() if key else ""


def analyser_aspiration(db: Session, profil_id: int) -> dict | None:
    """Analyse la faisabilité de l'aspiration (poste visé) d'un profil au regard des
    trajectoires de la population. Renvoie None si aucun poste visé n'est renseigné."""
    p = db.get(Profil, profil_id)
    if p is None:
        return None
    aspiration = (p.poste_vise or "").strip()
    if not aspiration:
        return None

    cur_poste = p.poste_actuel or ""
    cur_lvl, asp_lvl = _niveau(cur_poste), _niveau(aspiration)

    others = db.scalars(
        select(Profil).where(Profil.id != profil_id, Profil.poste_actuel.is_not(None))
    ).all()
    # « Role models » : même FILIÈRE que l'aspiration ET au moins à son niveau
    # (personnes ayant réellement atteint un poste comparable).
    modeles = [o for o in others
               if _similar(aspiration, o.poste_actuel) >= 0.5
               and _niveau(o.poste_actuel) >= asp_lvl]
    reachable = bool(modeles)

    depts = Counter(o.departement_key for o in modeles if o.departement_key)
    dom_dept = depts.most_common(1)[0][0] if depts else None
    lineaire = (dom_dept is None) or (dom_dept == p.departement_key)

    inter: Counter[str] = Counter()
    exemples: list[dict] = []
    for o in modeles[:20]:
        passes = [s.titre for s in db.scalars(
            select(ProfilStation).where(ProfilStation.profil_id == o.id)
            .order_by(ProfilStation.ordre)).all() if s.etat == StationEtat.PASSE]
        for t in passes:
            if cur_lvl < _niveau(t) < asp_lvl:
                inter[t] += 1
        if passes and len(exemples) < 3:
            exemples.append({"parcours": passes + [o.poste_actuel]})  # anonyme
    intermediaires = [t for t, _ in inter.most_common(3)]
    ecart = max(0, asp_lvl - cur_lvl)

    if not reachable:
        verdict = "a_defricher"
        explication = ("Aucun collaborateur n'occupe aujourd'hui un poste comparable dans les "
                       "données : trajectoire pionnière, à construire avec votre HRBP.")
    elif ecart >= 2:
        verdict = "ambitieuse"
        explication = (f"Aspiration ambitieuse : {ecart} niveaux au-dessus de votre poste actuel. "
                       f"{len(modeles)} collaborateur(s) l'occupent aujourd'hui")
        explication += (f", généralement après être passés par : {', '.join(intermediaires)}."
                        if intermediaires else ".")
    else:
        verdict = "accessible"
        explication = (f"Aspiration accessible : proche de votre niveau actuel. "
                       f"{len(modeles)} collaborateur(s) y sont déjà parvenus.")
    if reachable and not lineaire:
        explication += (" Trajectoire NON LINÉAIRE : elle implique une mobilité vers la filière "
                        f"« {_humaniser(dom_dept)} ».")

    return {
        "aspiration": aspiration,
        "poste_actuel": cur_poste,
        "reachable": reachable,
        "lineaire": lineaire,
        "ecart_niveau": ecart,
        "verdict": verdict,             # accessible | ambitieuse | a_defricher
        "nb_modeles": len(modeles),
        "intermediaires": intermediaires,
        "exemples": exemples,
        "explication": explication,
    }
