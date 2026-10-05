from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import date
from app.api.dependencies import get_read_only_db
from app.db.session import get_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import (
    BillingSummaryResponse,
    InvoiceCreate,
    InvoiceFilterParams,
    InvoiceResponse,
)

router = APIRouter(prefix="/clients/{client_id}/invoices", tags=["Faturamento"])
router_all = APIRouter(prefix="/invoices", tags=["Faturamento"])


@router_all.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar fatura",
    description="Cria uma fatura para um cliente existente.",
)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Cria uma fatura e retorna seus dados."""
    return InvoiceService.create_invoice(db, payload)


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
