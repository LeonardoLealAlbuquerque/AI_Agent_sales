from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.consulta import IdMixin

class ClientResponse(IdMixin):
    """Schema para retornar os dados básicos do cliente na API."""
    company_name: str
    cnpj: str
    status: str
    credit_limit: float

    class Config:
        # Permite que o Pydantic leia o objeto do banco de dados (SQLAlchemy) diretamente
        from_attributes = True 

class CreditAnalyticResponse(BaseModel):
    """Schema de resposta com a inteligência financeira do cliente."""
    client_id: int
    credit_limit: float = Field(..., description="Limite total concedido ao cliente")
    current_exposure: float = Field(..., description="Soma de faturas em aberto não canceladas")
    available_credit: float = Field(..., description="Crédito real disponível para novas compras")
    is_blocked: bool = Field(..., description="True se o cliente não pode comprar")
    block_reasons: List[str] = Field(
        default_factory=list, 
        description="Lista de motivos caso esteja bloqueado (ex: limite excedido, inativo)"
    )