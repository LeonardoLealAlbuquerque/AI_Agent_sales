from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from app.api.dependencies import get_read_only_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoicing import FaturasVencidasResponse, ResumoFaturamentoResponse

# Agrupando tudo sob o domínio de clientes
router = APIRouter(prefix="/clients/{client_id}/invoices", tags=["Faturamento"])

@router.get("/overdue", response_model=FaturasVencidasResponse)
def list_overdue_invoices(
    client_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_read_only_db)
):
    """Retorna as faturas vencidas e o saldo total devedor."""
    return InvoiceService.list_overdue_invoices(db, client_id, skip, limit)

@router.get("/summary", response_model=ResumoFaturamentoResponse)
def get_financial_summary(
    client_id: int,
    start: date,
    end: date,
    db: Session = Depends(get_read_only_db)
):
    """Agrega valores pagos, pendentes e cancelados em um período."""
    return InvoiceService.generate_financial_summary(db, client_id, start, end)
