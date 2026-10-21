"""table competence_evaluations (score d'acquisition par source, manager 1-10)

Revision ID: f6c1e2a4b3d7
Revises: e5b3c7d9a2f1
Create Date: 2026-08-05 16:35:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6c1e2a4b3d7"
down_revision: Union[str, Sequence[str], None] = "e5b3c7d9a2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "competence_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profil_competence_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=12), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("evaluateur_id", sa.Integer(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profil_competence_id"], ["profil_competences.id"]),
        sa.ForeignKeyConstraint(["evaluateur_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profil_competence_id", "source", name="uq_comp_eval_source"),
    )
    with op.batch_alter_table("competence_evaluations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_competence_evaluations_profil_competence_id"),
            ["profil_competence_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("competence_evaluations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_competence_evaluations_profil_competence_id"))

    op.drop_table("competence_evaluations")
