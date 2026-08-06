"""competence_evaluations.offre_id (contexte mission)

Revision ID: d4e8f1a2c6b9
Revises: f6c1e2a4b3d7
Create Date: 2026-08-06 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e8f1a2c6b9'
down_revision: Union[str, Sequence[str], None] = 'f6c1e2a4b3d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('competence_evaluations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('offre_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_competence_evaluations_offre_id'), ['offre_id'], unique=False)
        batch_op.create_foreign_key('fk_comp_eval_offre', 'offres', ['offre_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('competence_evaluations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_comp_eval_offre', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_competence_evaluations_offre_id'))
        batch_op.drop_column('offre_id')
