from typing import Optional, Sequence
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem as OrderItemModel
from app.schemas.order import OrderCreate, OrderItemCreate
# Assumindo que a relação no seu modelo Order se chame "items"

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def create(self, order_data: OrderCreate, total_amount: float) -> Order:
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
        self, order_id: int, item_data: OrderItemCreate, subtotal: float
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

    def calculate_total_amount(self, order_id: int) -> float:
        stmt = select(func.coalesce(func.sum(OrderItemModel.subtotal), 0.0)).where(
            OrderItemModel.order_id == order_id
        )
        return float(self.db.scalar(stmt) or 0.0)

    def update_order_total(self, order_id: int, total_amount: float) -> None:
        order = self.get_by_id(order_id)
        if order:
            order.total_amount = total_amount
            self.db.flush()

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