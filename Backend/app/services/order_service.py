from datetime import date
from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.order_repository import OrderRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemPatch,
    OrderItemResponse,
    OrderSummary,
    OrderDetail,
    DeliveryInfo,
    OrderItem,
)
from app.api.errors import BusinessRuleException, NotFoundException
from sqlalchemy.exc import IntegrityError

class OrderService:

    @staticmethod
    def create_order_item(
        db: Session, order_id: int, item_data: OrderItemCreate
    ) -> OrderItemResponse:
        repository = OrderRepository(db)
        if not repository.get_by_id(order_id):
            raise NotFoundException(f"Pedido {order_id} não encontrado.")

        subtotal = item_data.quantity * item_data.unit_price - item_data.discount
        try:
            item = repository.create_item(order_id, item_data, subtotal)
            repository.update_order_total(
                order_id, repository.calculate_total_amount(order_id)
            )
            db.commit()
            db.refresh(item)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível adicionar o item ao pedido."
            ) from exc

        return OrderItemResponse.model_validate(item)

    @staticmethod
    def update_order_item(
        db: Session,
        order_id: int,
        item_id: int,
        payload: OrderItemPatch,
    ) -> OrderItemResponse:
        repository = OrderRepository(db)
        if not repository.get_by_id(order_id):
            raise NotFoundException(f"Pedido {order_id} não encontrado.")

        item = repository.get_item_for_order(order_id, item_id)
        if not item:
            raise NotFoundException(f"Item {item_id} não encontrado no pedido {order_id}.")

        changes = payload.model_dump(exclude_unset=True)
        new_values = {
            "quantity": changes.get("quantity", item.quantity),
            "unit_price": changes.get("unit_price", item.unit_price),
            "discount": changes.get("discount", item.discount),
        }
        gross_amount = new_values["quantity"] * new_values["unit_price"]
        if new_values["discount"] > gross_amount:
            raise BusinessRuleException(
                "O desconto não pode superar o valor total do item."
            )

        try:
            for field_name, value in changes.items():
                setattr(item, field_name, value)
            item.subtotal = gross_amount - new_values["discount"]
            db.flush()
            repository.update_order_total(
                order_id, repository.calculate_total_amount(order_id)
            )
            db.commit()
            db.refresh(item)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível atualizar o item do pedido."
            ) from exc

        return OrderItemResponse.model_validate(item)

    @staticmethod
    def delete_order_item(db: Session, order_id: int, item_id: int) -> None:
        repository = OrderRepository(db)
        if not repository.get_by_id(order_id):
            raise NotFoundException(f"Pedido {order_id} não encontrado.")

        item = repository.get_item_for_order(order_id, item_id)
        if not item:
            raise NotFoundException(f"Item {item_id} não encontrado no pedido {order_id}.")
        if len(repository.list_items(order_id)) <= 1:
            raise BusinessRuleException(
                "O pedido deve manter pelo menos um item."
            )

        try:
            repository.delete_item(item)
            repository.update_order_total(
                order_id, repository.calculate_total_amount(order_id)
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível remover o item do pedido."
            ) from exc

    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> OrderDetail:
        """Valida o cliente, calcula subtotais e persiste o pedido com seus itens."""
        if not ClientRepository(db).get_by_id(order_data.client_id):
            raise NotFoundException(
                f"Cliente de ID {order_data.client_id} não encontrado no sistema."
            )

        total_amount = sum(
            item.quantity * item.unit_price - item.discount
            for item in order_data.items
        )

        try:
            order = OrderRepository(db).create(order_data, total_amount)
            order_id = order.id
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível cadastrar o pedido. Verifique os dados informados."
            ) from exc

        return OrderService.get_order_details(db, order_id)
    
    @staticmethod
    def _calculate_logistics(previsao: date, entrega_real: Optional[date]) -> DeliveryInfo:
        """Calcula o status de atraso baseado nas datas."""
        hoje = date.today()
        atraso_dias = 0
        
        # Se já foi entregue, comparamos a data real com a previsão
        if entrega_real:
            if entrega_real > previsao:
                atraso_dias = (entrega_real - previsao).days
        # Se não foi entregue, comparamos o dia de hoje com a previsão
        else:
            if hoje > previsao:
                atraso_dias = (hoje - previsao).days
                
        return DeliveryInfo(
            estimated_delivery_date=previsao,
            actual_delivery_date=entrega_real,
            is_delayed=atraso_dias > 0,
            delay_days=atraso_dias
        )

    @staticmethod
    def list_orders_by_client(
        db: Session, client_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrderSummary]:
        """Busca os pedidos e os empacota no schema de resumo."""
        repo = OrderRepository(db)
        pedidos_db = repo.buscar_pedidos_cliente(client_id, skip=skip, limit=limit)
        
        resultado = []
        for p in pedidos_db:
            # Aqui você pode somar do banco ou de uma propriedade calculada
            # Assumindo que você tem um campo total ou calcula iterando
            info_entrega = OrderService._calculate_logistics(p.estimated_delivery_date, p.delivery_date)
            
            resultado.append(OrderSummary(
                id=p.id,
                client_id=p.client_id,
                status=p.status,
                created_at=p.created_at,
                total_amount=p.total_amount, # Ajuste para o nome do campo real do seu model
                delivery_info=info_entrega
            ))
        return resultado

    @staticmethod
    def get_order_details(db: Session, pedido_id: int) -> OrderDetail:
        """Busca um pedido específico, com seus itens."""
        repo = OrderRepository(db)
        pedido = repo.obter_detalhes_pedido(pedido_id)
        
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado.")
            
        info_entrega = OrderService._calculate_logistics(pedido.estimated_delivery_date, pedido.delivery_date)
        
        itens_schema = [
            OrderItem(
                id=item.id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal
            ) for item in pedido.items
        ]
        
        return OrderDetail(
            id=pedido.id,
            client_id=pedido.client_id,
            status=pedido.status,
            created_at=pedido.created_at,
            total_amount=pedido.total_amount,
            delivery_info=info_entrega,
            items=itens_schema
        )