from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import date
from app.schemas.consult import IdMixin
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., ge=1, description="Identificador do produto.")
    product_name: str = Field(..., min_length=1, description="Nome do produto.")
    quantity: int = Field(1, ge=1, description="Quantidade solicitada.")
    unit_price: float = Field(..., ge=0, description="Preço unitário do produto.")
    discount: float = Field(0, ge=0, description="Desconto total aplicado ao item.")

    @field_validator("product_name")
    @classmethod
    def strip_product_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto não pode ficar vazio.")
        return value

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount > self.quantity * self.unit_price:
            raise ValueError("O desconto não pode superar o valor total do item.")
        return self


class OrderCreate(BaseModel):
    client_id: int = Field(..., ge=1, description="ID do cliente associado ao pedido.")
    created_at: date = Field(default_factory=date.today, description="Data de criação do pedido.")
    estimated_delivery_date: date = Field(..., description="Data prevista para entrega.")
    status: OrderStatus = Field(OrderStatus.PENDING, description="Status inicial do pedido.")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Itens do pedido.")


class OrderItemPatch(BaseModel):
    product_id: Optional[int] = Field(None, ge=1)
    product_name: Optional[str] = Field(None, min_length=1)
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)

    @field_validator("product_name")
    @classmethod
    def strip_product_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto não pode ficar vazio.")
        return value

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set or any(
            getattr(self, field_name) is None for field_name in self.model_fields_set
        ):
            raise ValueError("Informe ao menos um campo válido para atualização.")
        return self


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    discount: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderItem(IdMixin):
    """Schema para os produtos dentro de um pedido."""
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class DeliveryInfo(BaseModel):
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
    delivery_info: DeliveryInfo

    class Config:
        from_attributes = True

class OrderDetail(OrderSummary):
    """Usado para a visualização completa, herdando o resumo e adicionando itens."""
    items: List[OrderItem]