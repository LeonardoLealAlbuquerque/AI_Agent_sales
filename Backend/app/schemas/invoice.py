from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    client_id: int = Field(..., ge=1, description="ID do cliente associado à fatura.")
    amount: float = Field(..., gt=0, description="Valor positivo da fatura.", examples=[1500.0])
    due_date: date = Field(..., description="Data de vencimento no formato YYYY-MM-DD.")
    status: InvoiceStatus = Field(
        InvoiceStatus.PENDING,
        description="Status inicial da fatura.",
    )
    payment_date: Optional[date] = Field(
        None,
        description="Data de pagamento, se aplicável.",
    )


class InvoiceResponse(BaseModel):
    id: int
    client_id: int
    amount: float
    due_date: date
    payment_date: Optional[date]
    status: InvoiceStatus

    class Config:
        from_attributes = True

class OverdueInvoice(BaseModel):
    id: int
    amount: float
    due_date: date
    days_overdue: int
    critical_status: bool

class BillingMetricsSummary(BaseModel):
    paid_amount: float
    pending_amount: float
    canceled_amount: float
    total_invoices_count: int

class PeriodSummary(BaseModel):
    start: date
    end: date

class BillingSummaryResponse(BaseModel):
    period: PeriodSummary
    metrics: BillingMetricsSummary

class InvoiceFilterParams(BaseModel):
    search: Optional[str] = Field(
        None, description="Busca por nome, CNPJ ou ID da fatura"
    )
    client_id: Optional[int] = Field(None, description="Filtra por um cliente específico")
    status: Optional[InvoiceStatus] = Field(
        None, description="Filtra por status exato (PENDING, PAID, CANCELED)"
    )
    only_overdue: bool = Field(
        False, description="Se True, filtra apenas faturas pendentes com vencimento no passado"
    )
    
    min_amount: Optional[float] = Field(None, ge=0, description="Valor mínimo da fatura")
    max_amount: Optional[float] = Field(None, ge=0, description="Valor máximo da fatura")
    
    payment_date_start: Optional[date] = Field(
        None, description="Filtra faturas pagas a partir dessa data (YYYY-MM-DD)"
    )
    payment_date_end: Optional[date] = Field(
        None, description="Filtra faturas pagas até essa data (YYYY-MM-DD)"
    )
    
    skip: int = Field(0, ge=0)
    limit: int = Field(50, le=100)