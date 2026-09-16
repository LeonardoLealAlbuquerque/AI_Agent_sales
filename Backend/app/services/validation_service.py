from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.client import Client
from app.models.order import Order
from app.models.invoice import Invoice

class ValidationService:
    @staticmethod
    def validate_order_total(order: Order) -> float:
        if not order.items:
            return 0.0

        total = sum(item.subtotal for item in order.items)

        if total < 0:
            raise ValueError("Erro transacional: O total do pedido não pode ser negativo.")

        return total

    @staticmethod
    def validate_invoice_consistency(db: Session, invoice: Invoice) -> bool:
        if not invoice.order_id:
            return True

        # Realiza busca de pedido com SQLAlchemy
        order = db.scalar(select(Order).where(Order.id == invoice.order_id))
        if not order:
            raise ValueError(f"Inconsistência: O pedido {invoice.order_id} não existe para a fatura {invoice.id}.")

        client = db.scalar(select(Client).where(Client.id == order.client_id))
        if not client:
            raise ValueError("Inconsistência: O pedido vinculado está órfão de cliente.")

        if client.status != "ACTIVE":
            raise ValueError(
                f"Bloqueio de negócio: O cliente '{client.company_name}' não está ATIVO."
            )

        return True
        