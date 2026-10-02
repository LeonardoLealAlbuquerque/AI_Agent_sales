from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.api.dependencies import get_read_only_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceFilterParams, BillingSummaryResponse

router = APIRouter(prefix="/clients/{client_id}/invoices", tags=["Faturamento"])
router_all = APIRouter(prefix="/invoices", tags=["Faturamento"])


@router_all.get("/invoices")
def list_invoices(
    filters: InvoiceFilterParams = Depends(),
    db: Session = Depends(get_read_only_db),
):
    """Retorna faturas abertas de todos os clientes."""
    return InvoiceService.list_invoices(db, filters)

@router.get("/summary", response_model=BillingSummaryResponse)
def get_financial_summary(
    client_id: int,
    start: date,
    end: date,
    db: Session = Depends(get_read_only_db)
):
    """Agrega valores pagos, pendentes e cancelados em um período."""
    return InvoiceService.generate_financial_summary(db, client_id, start, end)
