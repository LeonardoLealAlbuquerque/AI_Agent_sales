from typing import Optional, Sequence
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.order import Order, OrderStatus
# Assumindo que a relação no seu modelo Order se chame "items"

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

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