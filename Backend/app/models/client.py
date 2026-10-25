from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Client(Base):
    __tablename__ = "clients"

    __table_args__ = (
        CheckConstraint("credit_limit >= 0", name="check_credit_limit_positive"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=False)
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)