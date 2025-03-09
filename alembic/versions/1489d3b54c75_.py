"""empty message

Revision ID: 1489d3b54c75
Revises: f90a2882c78b
Create Date: 2025-03-09 16:35:09.215860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1489d3b54c75'
down_revision: Union[str, None] = 'f90a2882c78b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rebalancing_data',
    sa.Column('data_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('input_data', sa.JSON(), nullable=False),
    sa.Column('output_data', sa.JSON(), nullable=False),
    sa.Column('rebalance_weight_list', sa.JSON(), nullable=False),
    sa.Column('nav_history', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('data_id')
    )
    op.create_index(op.f('ix_rebalancing_data_data_id'), 'rebalancing_data', ['data_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rebalancing_data_data_id'), table_name='rebalancing_data')
    op.drop_table('rebalancing_data')
    # ### end Alembic commands ###
