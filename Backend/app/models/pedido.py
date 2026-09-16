import enum
from datetime import date
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING)
    
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    client: Mapped["Client"] = relationship(backref="orders")