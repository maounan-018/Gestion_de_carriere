#!/usr/bin/env python3
"""
build_crosswalk.py — Construit le crosswalk (O*NET/SFIA → pivot ESCO).

À LANCER DEPUIS backend/ :
    python build_crosswalk.py

Aligne chaque compétence O*NET/SFIA sur sa compétence équivalente ESCO
(embeddings → reranker → validation LLM). Idempotent : relançable.
"""

import logging

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services import crosswalk_service


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    init_db()
    db = SessionLocal()
    try:
        crosswalk_service.build_crosswalk(db)
        print("\n=== ÉTAT DU CROSSWALK ===")
        for k, v in crosswalk_service.crosswalk_stats(db).items():
            print(f"  {k:<28} {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
