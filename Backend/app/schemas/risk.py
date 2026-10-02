from pydantic import BaseModel
from typing import List, Optional

class RuleInconsistency(BaseModel):
    rule_name: str
    description: str
    severity: str  

class ConsolidatedRisk(BaseModel):
    client_id: int
    total_exposure: float
    client_name: Optional[str] = None
    max_overdue_days: int
    open_orders_count: int
    open_orders_amount: float
    inconsistencies: List[RuleInconsistency] = []
    risk_level: Optional[str] = None  