"""besoins_recrutement (manager exprime, HRBP publie)

Revision ID: a1b2c3d4e5f6
Revises: d4e8f1a2c6b9
Create Date: 2026-08-07 09:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "d4e8f1a2c6b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "besoins_recrutement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("manager_user_id", sa.Integer(), nullable=False),
        sa.Column("fiche_id", sa.Integer(), nullable=True),
        sa.Column("poste", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("statut", sa.String(length=12), nullable=False, server_default="transmis"),
        sa.Column("hrbp_user_id", sa.Integer(), nullable=True),
        sa.Column("offre_id", sa.Integer(), nullable=True),
        sa.Column("motif_refus", sa.String(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["manager_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["fiche_id"], ["fiches.id"]),
        sa.ForeignKeyConstraint(["hrbp_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["offre_id"], ["offres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("besoins_recrutement", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_besoins_recrutement_manager_user_id"), ["manager_user_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_besoins_recrutement_fiche_id"), ["fiche_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_besoins_recrutement_statut"), ["statut"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_besoins_recrutement_offre_id"), ["offre_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("besoins_recrutement", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_besoins_recrutement_offre_id"))
        batch_op.drop_index(batch_op.f("ix_besoins_recrutement_statut"))
        batch_op.drop_index(batch_op.f("ix_besoins_recrutement_fiche_id"))
        batch_op.drop_index(batch_op.f("ix_besoins_recrutement_manager_user_id"))
    op.drop_table("besoins_recrutement")
