#!/usr/bin/env python3
"""
generate_fiches.py — Batch : génère + ancre + PERSISTE les fiches de poste.

À LANCER DEPUIS backend/ :
    python generate_fiches.py            # toute la cartographie (~165 fiches)
    python generate_fiches.py --limit 3  # test rapide (3 fiches)

Pour chaque métier de config/departements_metiers.yaml : génère la fiche
(mistral-nemo, grounded sur le graphe), ancre chaque compétence à une compétence
canonique du graphe, et enregistre Fiche + FicheCompetence. Idempotent (saute les
fiches déjà créées) et commit par fiche (reprise possible). Contenu SYNTHÉTIQUE.
"""

import sys
import logging

from sqlalchemy import select, func

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services import cartography_service, fiche_generation_service
from app.services.skill_search_service import search_skills
from app.models.fiche import Fiche, FicheCompetence, FicheSource

logger = logging.getLogger(__name__)

# Rubriques "liste de compétences" du gabarit -> catégorie déclarée.
_SKILL_SECTIONS = [
    ("competences_metiers", "metier"),
    ("competences_comportementales", "comportementale"),
    ("competences_transversales", "transversale"),
    ("methodologie_outils_technologies", "outil_technologie"),
]


def _persist(db, dept_key: str, gen: dict) -> Fiche:
    s = gen["sections"]
    fiche = Fiche(
        departement_key=dept_key, perimetre_bmci=s.get("perimetre_bmci", ""),
        famille_metier=s.get("famille_metier"), intitule_poste=s["intitule_poste"],
        code_poste=s.get("code_poste"), mission=s.get("mission"),
        activites_principales=s.get("activites_principales"), langues=s.get("langues"),
        indicateurs_performances=s.get("indicateurs_performances"),
        source=FicheSource.GENEREE, synthetique=True,
    )
    db.add(fiche)
    db.flush()  # -> fiche.id

    for section_key, categorie in _SKILL_SECTIONS:
        for libelle in [l.strip() for l in (s.get(section_key) or "").split("\n") if l.strip()]:
            matches = search_skills(db, libelle, k=1)   # ancrage graphe (canonique)
            m = matches[0] if matches else None
            db.add(FicheCompetence(
                fiche_id=fiche.id, libelle=libelle, categorie=categorie, implicite=False,
                skill_id=m["skill_id"] if m else None,
                skill_label_fr=m["label_fr"] if m else None,
                rerank_score=m.get("rerank_score") if m else None,
            ))
    return fiche


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    init_db()

    db = SessionLocal()
    try:
        existing = {(f.departement_key, f.intitule_poste)
                    for f in db.scalars(select(Fiche)).all()}
        todo = [(d["key"], d, m) for d in cartography_service.departements()
                for m in d.get("metiers", []) if (d["key"], m) not in existing]
        if limit:
            todo = todo[:limit]
        logger.info("À générer : %d fiches (%d déjà en base).", len(todo), len(existing))

        made = 0
        for dept_key, dept, metier in todo:
            gen = fiche_generation_service.generate_fiche(db, metier, dept)
            _persist(db, dept_key, gen)
            db.commit()
            made += 1
            logger.info("  [%d/%d] %s — %s", made, len(todo), dept["nom"], metier)

        total = db.scalar(select(func.count()).select_from(Fiche))
        print(f"\n=== {made} fiches générées cette exécution — {total} fiches en base ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
