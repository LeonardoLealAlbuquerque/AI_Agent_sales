import enum
from datetime import date
from sqlalchemy import ForeignKey, Date, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELED = "CANCELED"

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), 
        default=InvoiceStatus.PENDING, 
        nullable=False
    )

    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )

    order: Mapped["Order | None"] = relationship(backref="invoices")