"""add incremental conversation summary

Revision ID: 5b91c3e8a12f
Revises: c303966f53b0
Create Date: 2026-11-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b91c3e8a12f"
down_revision: Union[str, None] = "9bd72a4c61e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(sa.Column("summary", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("summary_through_message_id", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_column("summary_through_message_id")
        batch_op.drop_column("summary")
