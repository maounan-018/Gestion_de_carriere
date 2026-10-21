#!/usr/bin/env python3
"""
etl_sqlite_to_supabase.py — Copie des données SQLite -> PostgreSQL/Supabase.

RÔLE
    ETL idempotent (re-jouable) de la base locale SQLite vers la base Postgres
    pointée par DATABASE_URL. Le SCHÉMA doit déjà exister (créé par
    `python -m app.database.init_db` avec DATABASE_URL posé : tables ORM +
    index/uniques + tables vectorielles pgvector + HNSW).

    Étapes :
      1. TRUNCATE de toutes les tables cibles (RESTART IDENTITY CASCADE) — re-jouable.
      2. Copie des 29 tables relationnelles en ordre FK (SQLAlchemy Core, types
         bool/datetime adaptés automatiquement). Chaque table est chargée en
         INSERT multi-lignes chunkés (<= ~50k paramètres/statement) : l'auto-FK de
         `users.manager_id` se résout dans un même statement.
      3. Copie des embeddings vec_skills / vec_occupations (sqlite-vec -> pgvector)
         via COPY (vec_to_json -> format texte `[...]` accepté par le type vector).
      4. setval() des séquences SERIAL sur MAX(id) (évite les collisions de PK).
      5. Vérification : comptes source == cible pour chaque table.

USAGE
    # DATABASE_URL doit pointer sur Postgres (sinon on refuse) :
    #   backend/.env.local  ->  DATABASE_URL=postgresql://...pooler.supabase.com:5432/postgres?sslmode=require
    conda run -n bmci-carrieres python etl_sqlite_to_supabase.py

SÉCURITÉ
    Aucune donnée dangereuse migrée : mots de passe = hachages PBKDF2, jetons de
    session = SHA-256. DATABASE_URL (secret) vit dans .env.local (gitignoré).
"""

import sqlite3
import sys
import time

import sqlite_vec
from sqlalchemy import create_engine, insert, select, text

import app.models  # noqa: F401 — peuple Base.metadata
from app.core.config import settings
from app.database.base import Base

VEC_TABLES = [("vec_skills", "skill_id"), ("vec_occupations", "occupation_id")]


def _chunks(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def main() -> int:
    if settings.db_dialect != "postgresql":
        print(
            "ABANDON : DATABASE_URL ne pointe pas sur Postgres "
            f"(dialecte={settings.db_dialect}). Posez DATABASE_URL dans .env.local."
        )
        return 2

    src = create_engine(f"sqlite:///{settings.DB_PATH}", future=True)
    dst = create_engine(
        settings.sqlalchemy_url, connect_args={"prepare_threshold": None}, future=True
    )
    tables = list(Base.metadata.sorted_tables)
    t0 = time.time()

    # 1) TRUNCATE (re-jouable) — CASCADE couvre les tables vectorielles.
    allnames = ", ".join(t.name for t in tables) + ", vec_skills, vec_occupations"
    with dst.begin() as d:
        d.execute(text(f"TRUNCATE {allnames} RESTART IDENTITY CASCADE"))

    # 2) Tables relationnelles (ordre FK).
    print("=== tables relationnelles ===")
    for t in tables:
        with src.connect() as s:
            rows = [dict(r) for r in s.execute(select(t)).mappings().all()]
        if rows:
            size = max(1, 50000 // len(t.columns))
            with dst.begin() as d:
                for ch in _chunks(rows, size):
                    d.execute(insert(t).values(ch))
        print(f"  {t.name:26s} {len(rows):7d}")

    # 3) Embeddings (sqlite-vec -> pgvector via COPY).
    print("=== embeddings (COPY) ===")
    sc = sqlite3.connect(settings.DB_PATH)
    sc.enable_load_extension(True)
    sqlite_vec.load(sc)
    sc.enable_load_extension(False)
    raw = dst.raw_connection()
    try:
        for vt, key in VEC_TABLES:
            data = sc.execute(f"SELECT {key}, vec_to_json(embedding) FROM {vt}").fetchall()
            cur = raw.driver_connection.cursor()
            with cur.copy(f"COPY {vt} ({key}, embedding) FROM STDIN") as cp:
                for k, emb in data:
                    cp.write_row((k, emb))
            raw.commit()
            print(f"  {vt:26s} {len(data):7d}")
    finally:
        raw.close()

    # 4) Reset des séquences SERIAL.
    with dst.begin() as d:
        for t in tables:
            pk = list(t.primary_key.columns)
            if len(pk) == 1 and pk[0].name == "id":
                d.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{t.name}','id'), "
                        f"GREATEST((SELECT COALESCE(MAX(id),1) FROM {t.name}),1))"
                    )
                )

    # 5) Vérification des comptes (source == cible, tables relationnelles + vec).
    print("=== vérification comptes source == cible ===")
    ok = True
    with src.connect() as s, dst.connect() as d:
        for t in tables:
            s_n = s.execute(text(f"SELECT COUNT(*) FROM {t.name}")).scalar()
            p_n = d.execute(text(f"SELECT COUNT(*) FROM {t.name}")).scalar()
            if s_n != p_n:
                ok = False
                print(f"  !! DIFF {t.name}: sqlite={s_n} pg={p_n}")
        for vt, _ in VEC_TABLES:
            s_n = sc.execute(f"SELECT COUNT(*) FROM {vt}").fetchone()[0]  # sc = sqlite-vec chargé
            p_n = d.execute(text(f"SELECT COUNT(*) FROM {vt}")).scalar()
            if s_n != p_n:
                ok = False
                print(f"  !! DIFF {vt}: sqlite={s_n} pg={p_n}")
    print(f"{'TOUT CONCORDE' if ok else 'DIVERGENCES'} — {time.time()-t0:.1f}s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
