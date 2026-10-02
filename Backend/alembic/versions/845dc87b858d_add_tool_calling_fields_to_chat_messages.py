"""add tool calling fields to chat_messages

Revision ID: 845dc87b858d
Revises: c303966f53b0
Create Date: 2026-09-30 19:14:41.409522

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '845dc87b858d'
down_revision: Union[str, None] = 'c303966f53b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema changes were already applied by revision 68c07170dca3."""
    pass


def downgrade() -> None:
    """No schema changes were made by this revision."""
    pass
