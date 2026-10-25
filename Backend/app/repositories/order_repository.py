from typing import Optional, Sequence
from datetime import date
from decimal import Decimal
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.order import Order, OrderStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.order_item import OrderItem as OrderItemModel
from app.schemas.order import OrderCreate, OrderItemCreate
# Assumindo que a relação no seu modelo Order se chame "items"

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def create(self, order_data: OrderCreate, total_amount: Decimal) -> Order:
        """Adiciona um pedido e seus itens à sessão; o service confirma a transação."""
        order = Order(
            client_id=order_data.client_id,
            status=order_data.status,
            created_at=order_data.created_at,
            total_amount=total_amount,
            estimated_delivery_date=order_data.estimated_delivery_date,
        )
        self.db.add(order)
        self.db.flush()

        self.db.add_all([
            OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                discount=item.discount,
                subtotal=item.quantity * item.unit_price - item.discount,
            )
            for item in order_data.items
        ])
        self.db.flush()
        return order

    def get_item_for_order(self, order_id: int, item_id: int) -> Optional[OrderItemModel]:
        stmt = select(OrderItemModel).where(
            OrderItemModel.order_id == order_id,
            OrderItemModel.id == item_id,
        )
        return self.db.scalar(stmt)

    def create_item(
        self, order_id: int, item_data: OrderItemCreate, subtotal: Decimal
    ) -> OrderItemModel:
        item = OrderItemModel(
            order_id=order_id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            unit_price=item_data.unit_price,
            quantity=item_data.quantity,
            discount=item_data.discount,
            subtotal=subtotal,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def list_items(self, order_id: int) -> Sequence[OrderItemModel]:
        stmt = select(OrderItemModel).where(OrderItemModel.order_id == order_id)
        return self.db.scalars(stmt).all()

    def delete_item(self, item: OrderItemModel) -> None:
        self.db.delete(item)
        self.db.flush()

    def calculate_total_amount(self, order_id: int) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(OrderItemModel.subtotal), Decimal("0.00"))
        ).where(
            OrderItemModel.order_id == order_id
        )
        return self.db.scalar(stmt) or Decimal("0.00")

    def update_order_total(self, order_id: int, total_amount: Decimal) -> None:
        order = self.get_by_id(order_id)
        if order:
            order.total_amount = total_amount
            self.db.flush()

    def calculate_open_order_summary(self, client_id: int) -> tuple[int, Decimal]:
        """Returns open-order count and the amount not covered by active invoices."""
        invoiced_amounts = (
            select(
                Invoice.order_id.label("order_id"),
                Invoice.client_id.label("client_id"),
                func.sum(Invoice.amount).label("invoiced_amount"),
            )
            .where(
                Invoice.order_id.is_not(None),
                Invoice.status != InvoiceStatus.CANCELED,
            )
            .group_by(Invoice.order_id, Invoice.client_id)
            .subquery()
        )
        invoiced_amount = func.coalesce(
            invoiced_amounts.c.invoiced_amount, Decimal("0.00")
        )
        unbilled_amount = case(
            (Order.total_amount > invoiced_amount, Order.total_amount - invoiced_amount),
            else_=Decimal("0.00"),
        )

        stmt = select(
            func.count(Order.id),
            func.coalesce(func.sum(unbilled_amount), Decimal("0.00")),
        ).outerjoin(
            invoiced_amounts,
            (invoiced_amounts.c.order_id == Order.id)
            & (invoiced_amounts.c.client_id == Order.client_id),
        ).where(
            Order.client_id == client_id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.SHIPPED]),
        )
        count, amount = self.db.execute(stmt).one()
        return int(count), amount

    def buscar_pedidos_cliente(
        self, 
        client_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[OrderStatus] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Sequence[Order]:
        """
        [T029] Consulta paginada de pedidos de um cliente, com filtros dinâmicos 
        por status e intervalo de datas.
        """
        # Começamos com a query base
        stmt = select(Order).where(Order.client_id == client_id)
        
        # Adicionamos filtros apenas se o usuário (ou a IA) os forneceu
        if status:
            stmt = stmt.where(Order.status == status)
        if data_inicio:
            stmt = stmt.where(Order.created_at >= data_inicio)
        if data_fim:
            stmt = stmt.where(Order.created_at <= data_fim)
            
        # Aplica a paginação no final
        stmt = stmt.offset(skip).limit(limit)
        
        return self.db.scalars(stmt).all()

    def obter_detalhes_pedido(self, pedido_id: int) -> Optional[Order]:
        """
        [T030] Busca os detalhes de um pedido específico, trazendo todos 
        os itens associados em uma única viagem ao banco de dados.
        """
        stmt = (
            select(Order)
            .options(joinedload(Order.items)) # Eager loading dos itens
            .where(Order.id == pedido_id)
        )
        return self.db.scalar(stmt)