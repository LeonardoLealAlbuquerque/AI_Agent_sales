from sqlalchemy import ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("discount >= 0", name="check_discount_positive"),
        CheckConstraint("subtotal >= 0", name="check_subtotal_positive"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Chaves estrangeiras
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(nullable=False, index=True) 
    product_name: Mapped[str] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)

    order: Mapped["Order"] = relationship(backref="items")