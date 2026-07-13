#!/usr/bin/env python3
"""
ingest_referentiels.py — Orchestrateur d'ingestion des référentiels de compétences.

À LANCER DEPUIS backend/ :
    python ingest_referentiels.py

Enchaîne : création du schéma → chargement des référentiels disponibles
(O*NET maintenant ; ESCO/SFIA dès que téléchargés) → vectorisation du graphe.
Idempotent : relançable sans dupliquer.
"""

import sys
import logging

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services.referentiels import esco_loader, onet_loader, graph_builder


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    skip_embed = "--skip-embed" in sys.argv     # charge sans vectoriser (validation rapide)
    init_db()

    db = SessionLocal()
    try:
        # --- Référentiels (idempotents) ---
        esco_loader.load_esco(db)   # pivot multilingue FR/EN
        onet_loader.load_onet(db)   # richesse métier (EN, FR à traduire)
        # from app.services.referentiels import sfia_loader
        # sfia_loader.load_sfia(db)

        # --- Vectorisation (embeddings -> vec_skills) — longue sur ESCO (~14k) ---
        if skip_embed:
            logging.info("Vectorisation SAUTÉE (--skip-embed).")
        else:
            graph_builder.embed_missing_skills(db)

        print("\n=== ÉTAT DU GRAPHE DE COMPÉTENCES ===")
        for k, v in graph_builder.graph_stats(db).items():
            print(f"  {k:<24} {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
