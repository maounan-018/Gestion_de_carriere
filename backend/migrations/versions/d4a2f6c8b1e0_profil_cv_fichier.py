"""profils : cv_filename + cv_uploaded_at (CV du collaborateur conservé)

Revision ID: d4a2f6c8b1e0
Revises: c3f1a9b7e2d4
Create Date: 2026-08-05 15:05:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a2f6c8b1e0"
down_revision: Union[str, Sequence[str], None] = "c3f1a9b7e2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("profils", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cv_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("cv_uploaded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("profils", schema=None) as batch_op:
        batch_op.drop_column("cv_uploaded_at")
        batch_op.drop_column("cv_filename")
