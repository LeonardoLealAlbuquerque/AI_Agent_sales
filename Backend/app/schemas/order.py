from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from app.schemas.consulta import IdMixin

class ItemPedido(IdMixin):
    """Schema para os produtos dentro de um pedido."""
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class EntregaInfo(BaseModel):
    """Encapsula a inteligência de logística do pedido."""
    estimated_delivery_date: date
    actual_delivery_date: Optional[date] = None
    is_delayed: bool = Field(default=False, description="True se a entrega está atrasada")
    delay_days: int = Field(default=0, description="Dias de atraso em relação à previsão")

class OrderSummary(IdMixin):
    """Usado para listagem rápida (sem carregar os itens)."""
    client_id: int
    status: str
    created_at: date
    total_amount: float
    delivery_info: EntregaInfo

    class Config:
        from_attributes = True

class OrderDetail(OrderSummary):
    """Usado para a visualização completa, herdando o resumo e adicionando itens."""
    items: List[ItemPedido]