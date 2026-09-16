from pydantic import BaseModel
from typing import List, Optional

class InconsistenciaRegra(BaseModel):
    rule_name: str
    description: str
    severity: str  # Ex: "ALTA", "MEDIA", "BAIXA"

class RiscoConsolidado(BaseModel):
    client_id: int
    total_exposure: float
    max_overdue_days: int
    open_orders_count: int
    open_orders_amount: float
    inconsistencies: List[InconsistenciaRegra] = []
    risk_level: Optional[str] = None  # Ex: "BAIXO", "MEDIO", "ALTO"