"""table entretien_syntheses (synthèse de préparation d'entretien persistée)

Revision ID: e5b3c7d9a2f1
Revises: d4a2f6c8b1e0
Create Date: 2026-08-05 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5b3c7d9a2f1'
down_revision: Union[str, Sequence[str], None] = 'd4a2f6c8b1e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('entretien_syntheses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('profil_id', sa.Integer(), nullable=False),
    sa.Column('synthese', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['profil_id'], ['profils.id']),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entretien_syntheses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entretien_syntheses_profil_id'), ['profil_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('entretien_syntheses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entretien_syntheses_profil_id'))

    op.drop_table('entretien_syntheses')
