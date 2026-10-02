from datetime import date
from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderSummary, OrderDetail, DeliveryInfo, OrderItem
from app.api.errors import NotFoundException

class OrderService:
    
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