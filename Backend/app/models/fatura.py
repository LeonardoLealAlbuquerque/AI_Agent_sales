from datetime import date
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Vencimento (Obrigatório)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Data de Pagamento (Opcional, pois pode não estar paga ainda)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Pedido Opcional (Chave estrangeira que aceita nulo)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)

    # Configuração de relacionamento para uso no código Python
    order: Mapped["Order | None"] = relationship(backref="invoices")