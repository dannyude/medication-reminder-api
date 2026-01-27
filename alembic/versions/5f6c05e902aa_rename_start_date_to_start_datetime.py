"""rename start_date to start_datetime

Revision ID: 5f6c05e902aa
Revises: b3d5eeee5e84
Create Date: 2026-01-24 19:12:11.436945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f6c05e902aa'
down_revision: Union[str, Sequence[str], None] = 'b3d5eeee5e84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename start_date -> start_datetime
    op.alter_column('medications', 'start_date', new_column_name='start_datetime') # type: ignore

    # Rename end_date -> end_datetime
    op.alter_column('medications', 'end_date', new_column_name='end_datetime') # type: ignore