"""table analyses_rh (persistance analyse stratégique HRBP)

Revision ID: c3f1a9b7e2d4
Revises: 2571397c720c
Create Date: 2026-08-05 14:20:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f1a9b7e2d4"
down_revision: Union[str, Sequence[str], None] = "2571397c720c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "analyses_rh",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("synthese", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("analyses_rh", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_analyses_rh_scope"), ["scope"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("analyses_rh", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_analyses_rh_scope"))

    op.drop_table("analyses_rh")
