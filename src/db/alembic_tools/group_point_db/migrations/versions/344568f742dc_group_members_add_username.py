"""empty message

Revision ID: 344568f742dc
Revises: 
Create Date: 2025-02-13 16:44:08.371886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '344568f742dc_group_members_add_username.py'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('group_members')]

    if 'username' not in columns:
        op.add_column('group_members', sa.Column('username', sa.String(), nullable=True))


def downgrade() -> None:
    pass
