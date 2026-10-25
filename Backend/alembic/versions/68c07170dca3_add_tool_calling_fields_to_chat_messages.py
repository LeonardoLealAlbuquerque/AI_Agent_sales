"""add tool calling fields to chat_messages

Revision ID: 68c07170dca3
Revises: 8f1c2d3e4a5b
Create Date: 2026-09-30 19:13:58.129818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68c07170dca3'
down_revision: Union[str, None] = '8f1c2d3e4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    for table_name in ("invoices", "order_items", "orders"):
        if connection.scalar(sa.text(f"SELECT COUNT(*) FROM {table_name}")):
            raise RuntimeError(
                f"Cannot safely migrate {table_name}: existing rows do not contain "
                "values for the required new fields. Reconcile these records before "
                "retrying the migration."
            )

    with op.batch_alter_table("chat_messages") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("tool_calls", sa.JSON(), nullable=True))
        batch_op.alter_column("content", existing_type=sa.Text(), nullable=True)

    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column("client_id", sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column("amount", sa.Float(), nullable=False))
        batch_op.add_column(
            sa.Column(
                "status",
                sa.Enum("PENDING", "PAID", "CANCELED", name="invoicestatus"),
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            "fk_invoices_client_id_clients",
            "clients",
            ["client_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.create_index(
        op.f("ix_invoices_client_id"), "invoices", ["client_id"], unique=False
    )

    with op.batch_alter_table("order_items") as batch_op:
        batch_op.add_column(sa.Column("product_name", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("unit_price", sa.Float(), nullable=False))

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.Date(), nullable=False))
        batch_op.add_column(sa.Column("total_amount", sa.Float(), nullable=False))
        batch_op.add_column(
            sa.Column("estimated_delivery_date", sa.Date(), nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_column("estimated_delivery_date")
        batch_op.drop_column("total_amount")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("order_items") as batch_op:
        batch_op.drop_column("unit_price")
        batch_op.drop_column("product_name")

    op.drop_index(op.f("ix_invoices_client_id"), table_name="invoices")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_constraint("fk_invoices_client_id_clients", type_="foreignkey")
        batch_op.drop_column("status")
        batch_op.drop_column("amount")
        batch_op.drop_column("client_id")

    with op.batch_alter_table("chat_messages") as batch_op:
        batch_op.alter_column("content", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("tool_calls")
        batch_op.drop_column("name")
