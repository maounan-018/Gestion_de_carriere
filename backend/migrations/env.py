"""Alembic env — BMCI Gestion des Carrières.

Réutilise le moteur de l'application (sqlite-vec chargé, bonne URL) et Base.metadata.
IMPORTANT : les tables vectorielles sqlite-vec (vec_*) sont créées hors ORM par
init_db — on les EXCLUT des migrations (include_object) pour qu'Alembic ne tente
jamais de les modifier/supprimer.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context

# backend/ sur le sys.path pour importer le package `app`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.models  # noqa: F401 — enregistre toutes les tables
from app.database.base import Base
from app.database.session import engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Ignore les tables vectorielles sqlite-vec (vec_skills, vec_occupations et
    leurs tables internes vec_*_chunks/rowids/...), hors périmètre ORM."""
    if type_ == "table" and name.startswith("vec_"):
        return False
    return True


# render_as_batch (recréation de table pour ALTER) est un contournement SQLITE only.
# Postgres supporte ALTER TABLE nativement → batch désactivé hors SQLite.
_IS_SQLITE = engine.dialect.name == "sqlite"


def run_migrations_offline() -> None:
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        render_as_batch=_IS_SQLITE,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            render_as_batch=_IS_SQLITE,  # SQLite : ALTER via batch
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
