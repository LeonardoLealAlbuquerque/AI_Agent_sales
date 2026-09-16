from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class IdMixin(BaseModel):
    """Schema compartilhado para identificação de recursos."""
    id: int = Field(..., description="Identificador único do registro")

class PaginationParams(BaseModel):
    """Schema compartilhado para paginação de resultados nas rotas GET."""
    skip: int = Field(0, ge=0, description="Número de registros para pular (offset)")
    limit: int = Field(100, ge=1, le=1000, description="Limite máximo de registros retornados por página")

class DateReferenceParams(BaseModel):
    """Schema compartilhado para filtros de intervalo de datas."""
    start_date: Optional[date] = Field(None, description="Data de início do período de busca")
    end_date: Optional[date] = Field(None, description="Data de fim do período de busca")

class GenericFilterParams(BaseModel):
    """Schema compartilhado para buscas genéricas em texto e status."""
    q: Optional[str] = Field(None, description="Termo de busca livre (ex: nome, documento)")
    status: Optional[str] = Field(None, description="Filtro exato por status (ex: ACTIVE, PENDING)")