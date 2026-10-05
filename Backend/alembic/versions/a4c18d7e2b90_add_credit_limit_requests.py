"""add credit limit review requests

Revision ID: a4c18d7e2b90
Revises: 845dc87b858d
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c18d7e2b90"
down_revision: Union[str, None] = "845dc87b858d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credit_limit_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("current_limit", sa.Float(), nullable=False),
        sa.Column("requested_limit", sa.Float(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_credit_limit_requests_client_id",
        "credit_limit_requests",
        ["client_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_credit_limit_requests_client_id", table_name="credit_limit_requests")
    op.drop_table("credit_limit_requests")