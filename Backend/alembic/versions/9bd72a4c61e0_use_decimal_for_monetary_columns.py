"""synchronize current schema and use decimal types for monetary columns

Revision ID: 9bd72a4c61e0
Revises: a4c18d7e2b90
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9bd72a4c61e0"
down_revision: Union[str, None] = "a4c18d7e2b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MONETARY_TYPE = sa.Numeric(precision=15, scale=2)

SCHEMA_ADDITIONS = {
    "invoices": {
        "client_id": sa.Column("client_id", sa.Integer(), nullable=False),
        "amount": sa.Column("amount", MONETARY_TYPE, nullable=False),
        "status": sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "CANCELED", name="invoicestatus"),
            nullable=False,
        ),
    },
    "orders": {
        "created_at": sa.Column("created_at", sa.Date(), nullable=False),
        "total_amount": sa.Column("total_amount", MONETARY_TYPE, nullable=False),
        "estimated_delivery_date": sa.Column(
            "estimated_delivery_date", sa.Date(), nullable=False
        ),
    },
    "order_items": {
        "product_name": sa.Column("product_name", sa.String(), nullable=False),
        "unit_price": sa.Column("unit_price", MONETARY_TYPE, nullable=False),
    },
}

MONETARY_COLUMNS = {
    "clients": ("credit_limit",),
    "invoices": ("amount",),
    "orders": ("total_amount",),
    "order_items": ("unit_price", "discount", "subtotal"),
    "credit_limit_requests": ("current_limit", "requested_limit"),
}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    for table_name, additions in SCHEMA_ADDITIONS.items():
        existing_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        missing_columns = set(additions) - existing_columns
        if missing_columns:
            row_count = connection.scalar(
                sa.text(f"SELECT COUNT(*) FROM {table_name}")
            )
            if row_count:
                missing = ", ".join(sorted(missing_columns))
                raise RuntimeError(
                    f"Cannot safely migrate {table_name}: existing rows cannot be "
                    f"backfilled for missing columns ({missing}). Reconcile these "
                    "records before retrying the migration."
                )

            with op.batch_alter_table(table_name) as batch_op:
                for column_name in sorted(missing_columns):
                    batch_op.add_column(additions[column_name])

                if table_name == "invoices" and "client_id" in missing_columns:
                    batch_op.create_foreign_key(
                        "fk_invoices_client_id_clients",
                        "clients",
                        ["client_id"],
                        ["id"],
                        ondelete="CASCADE",
                    )

            if table_name == "invoices" and "client_id" in missing_columns:
                op.create_index(
                    "ix_invoices_client_id", "invoices", ["client_id"], unique=False
                )

    inspector = sa.inspect(connection)
    for table_name, column_names in MONETARY_COLUMNS.items():
        columns = {
            column["name"]: column
            for column in inspector.get_columns(table_name)
        }
        columns_to_convert = []
        for column_name in column_names:
            column_type = columns[column_name]["type"]
            if (
                not isinstance(column_type, sa.Numeric)
                or column_type.precision != 15
                or column_type.scale != 2
            ):
                columns_to_convert.append((column_name, column_type))

        if columns_to_convert:
            with op.batch_alter_table(table_name) as batch_op:
                for column_name, existing_type in columns_to_convert:
                    batch_op.alter_column(
                        column_name,
                        existing_type=existing_type,
                        type_=MONETARY_TYPE,
                    )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    for table_name, column_names in reversed(tuple(MONETARY_COLUMNS.items())):
        columns = {
            column["name"]: column
            for column in inspector.get_columns(table_name)
        }
        columns_to_convert = [
            column_name
            for column_name in column_names
            if isinstance(columns[column_name]["type"], sa.Numeric)
        ]
        if columns_to_convert:
            with op.batch_alter_table(table_name) as batch_op:
                for column_name in columns_to_convert:
                    batch_op.alter_column(
                        column_name,
                        existing_type=MONETARY_TYPE,
                        type_=sa.Float(),
                    )
