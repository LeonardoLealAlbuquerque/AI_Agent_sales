"""merge_branches

Revision ID: c303966f53b0
Revises: 68c07170dca3
Create Date: 2026-09-30 19:14:14.818188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c303966f53b0'
down_revision: Union[str, None] = '68c07170dca3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
