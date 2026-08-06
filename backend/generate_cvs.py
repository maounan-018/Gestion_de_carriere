#!/usr/bin/env python3
"""
generate_cvs.py — Batch : génère un CV PDF pour chaque profil.

À LANCER DEPUIS backend/ :
    python generate_cvs.py               # tous les profils (~343)
    python generate_cvs.py --limit 5     # test rapide (5 profils)
    python generate_cvs.py --missing     # seulement les profils sans CV

Pour chaque profil, produit `data/cv_profil/{id}.pdf` à partir de ses données
RÉELLES (parcours + compétences + projet d'évolution) et marque `cv_filename`
→ le CV apparaît côté manager / HRBP comme un CV téléversé. Idempotent
(régénère à l'identique). Commit par profil (reprise possible).
"""

import sys
import logging

from sqlalchemy import select, func

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.models.profil import Profil
from app.services import cv_generation_service as cv

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    only_missing = "--missing" in sys.argv
    init_db()

    db = SessionLocal()
    try:
        profils = list(db.scalars(select(Profil).order_by(Profil.id)).all())
        if only_missing:
            profils = [p for p in profils if not p.cv_filename]
        if limit:
            profils = profils[:limit]
        logger.info("À générer : %d CV.", len(profils))

        made, failed = 0, 0
        for i, p in enumerate(profils, 1):
            try:
                cv.generer_cv_profil(db, p.id)
                made += 1
                if i % 25 == 0 or i == len(profils):
                    logger.info("  [%d/%d] CV générés…", i, len(profils))
            except Exception as e:  # noqa: BLE001
                db.rollback()
                failed += 1
                logger.warning("  ÉCHEC profil %d : %s (sauté)", p.id, str(e)[:120])

        avec_cv = db.scalar(select(func.count()).select_from(Profil).where(Profil.cv_filename.is_not(None)))
        print(f"\n=== {made} générés, {failed} sautés — {avec_cv} profils avec CV en base ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
