from pydantic import BaseModel
from datetime import date
from typing import List

class FaturaVencida(BaseModel):
    id: int
    amount: float
    due_date: date
    days_overdue: int
    critical_status: bool

class FaturasVencidasResponse(BaseModel):
    client_id: int
    total_overdue_balance: float
    overdue_invoices: List[FaturaVencida]

class ResumoFaturamentoMetrics(BaseModel):
    paid_amount: float
    pending_amount: float
    canceled_amount: float
    total_invoices_count: int

class PeriodoResumo(BaseModel):
    start: date
    end: date

class ResumoFaturamentoResponse(BaseModel):
    period: PeriodoResumo
    metrics: ResumoFaturamentoMetrics