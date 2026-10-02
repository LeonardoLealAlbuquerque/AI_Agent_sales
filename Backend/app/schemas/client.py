import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.schemas.consult import IdMixin

class ClientResponse(IdMixin):
    """Schema para retornar os dados básicos do cliente na API."""
    company_name: str
    cnpj: str
    status: str
    credit_limit: float

    class Config:
        # Permite que o Pydantic leia o objeto do banco de dados (SQLAlchemy) diretamente
        from_attributes = True 


class ClientCreate(BaseModel):
    """Dados necessários para cadastrar um cliente pela API."""
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Razão social ou nome da empresa.",
        examples=["Tech Solutions LTDA"],
    )
    cnpj: str = Field(
        ...,
        description="CNPJ com ou sem pontuação; será armazenado apenas com dígitos.",
        examples=["12.345.678/0001-95"],
    )
    credit_limit: float = Field(
        0,
        ge=0,
        description="Limite de crédito inicial. Não pode ser negativo.",
        examples=[5000.0],
    )

    @field_validator("company_name")
    @classmethod
    def strip_company_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome da empresa não pode ficar vazio.")
        return value

    @field_validator("cnpj")
    @classmethod
    def normalize_cnpj(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) != 14:
            raise ValueError("CNPJ deve conter exatamente 14 dígitos.")
        return digits


class ClientFilterParams(BaseModel):
    client_id: Optional[int] = Field(None, ge=1)
    name: Optional[str] = Field(None, min_length=1)
    cnpj: Optional[str] = Field(None, min_length=1, max_length=32)
    credit_limit: Optional[float] = Field(None, ge=0)
    min_credit_limit: Optional[float] = Field(None, ge=0)
    max_credit_limit: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, min_length=1)
    limit: int = Field(50, ge=1, le=100)
    skip: int = Field(0, ge=0)

    @field_validator("cnpj")
    @classmethod
    def normalize_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        if not digits:
            raise ValueError("CNPJ deve conter ao menos um dígito.")
        return digits

    @field_validator("name", "status")
    @classmethod
    def strip_text_filters(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else None

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