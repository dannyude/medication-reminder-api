"""force_add_reminder_times_column

Revision ID: 59e231269631
Revises: 7691679c0781
Create Date: 2026-01-26 13:37:03.719693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '59e231269631'
down_revision: Union[str, Sequence[str], None] = '7691679c0781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade() -> None:
    # Forcefully add the missing column to 'medications'
    op.add_column(
        'medications',
        sa.Column('reminder_times', sa.JSON(), nullable=True)
    )

def downgrade() -> None:
    # Allow undoing this change if needed
    op.drop_column('medications', 'reminder_times')
