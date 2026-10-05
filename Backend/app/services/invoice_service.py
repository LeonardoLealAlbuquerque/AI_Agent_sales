from datetime import date
from typing import Any
from sqlalchemy.orm import Session
from app.schemas.invoice import InvoiceFilterParams
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.api.errors import NotFoundException, BusinessRuleException
from sqlalchemy.exc import IntegrityError
from app.models.invoice import InvoiceStatus

class InvoiceService:
    @staticmethod
    def create_invoice(db: Session, invoice_data: InvoiceCreate) -> InvoiceResponse:
        """Valida o cliente, persiste a fatura e retorna sua representação pública."""
        if not ClientRepository(db).get_by_id(invoice_data.client_id):
            raise NotFoundException(
                f"Cliente de ID {invoice_data.client_id} não encontrado no sistema."
            )

        try:
            invoice = InvoiceRepository(db).create(invoice_data)
            db.commit()
            db.refresh(invoice)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível cadastrar a fatura. Verifique os dados informados."
            ) from exc

        return InvoiceResponse.model_validate(invoice)

    @staticmethod
    def _calculate_days_overdue(vencimento: date) -> int:
        hoje = date.today()
        if hoje > vencimento:
            return (hoje - vencimento).days
        return 0
    
    @staticmethod
    def list_invoices(db: Session, filters: InvoiceFilterParams) -> dict[str, Any]:
        """
        Lista faturas agrupadas por cliente com suporte a busca genérica,
        filtros por status, cliente específico e flag de faturas vencidas.
        """
        rows = InvoiceRepository(db).get_filtered_invoices(filters)
        
        clients: dict[int, dict[str, Any]] = {}
        total_amount = 0.0
        total_overdue_amount = 0.0

        for client, invoice in rows:
            atraso = InvoiceService._calculate_days_overdue(invoice.due_date)
            is_critical = atraso > 30

            client_data = clients.setdefault(
                client.id,
                {
                    "client_id": client.id,
                    "client_name": client.company_name,
                    "open_balance": 0.0,
                    "invoices": [],
                },
            )
            
            client_data["open_balance"] += invoice.amount
            client_data["invoices"].append({
                "id": invoice.id,
                "amount": invoice.amount,
                "due_date": invoice.due_date,
                "status": invoice.status,
                "days_overdue": atraso,
                "critical_status": is_critical
            })
            
            total_amount += invoice.amount
            if atraso > 0:
                total_overdue_amount += invoice.amount

        return {
            "total_clients": len(clients),
            "total_invoices_count": len(rows),
            "total_amount": total_amount,
            "total_overdue_amount": total_overdue_amount,
            "clients": list(clients.values()),
        }
    
    @staticmethod
    def _calculate_days_overdue(vencimento: date) -> int:
        """Calcula dias corridos de atraso em relação à data atual."""
        hoje = date.today()
        if hoje > vencimento:
            return (hoje - vencimento).days
        return 0

    @staticmethod
    def generate_financial_summary(db: Session, client_id: int, data_inicio: date, data_fim: date) -> dict:
        """
        [T037] Formata a agregação do banco em um relatório consolidado.
        """
        repo = InvoiceRepository(db)
        agregados = repo.get_billing_summary_by_period(client_id, data_inicio, data_fim)
        
        resumo = {
            "period": {"start": data_inicio, "end": data_fim},
            "metrics": {
                "paid_amount": 0.0,
                "pending_amount": 0.0,
                "canceled_amount": 0.0,
                "total_invoices_count": 0
            }
        }
        
        for status, qtd, total in agregados:
            resumo["metrics"]["total_invoices_count"] += qtd
            
            if status == InvoiceStatus.PAID:
                resumo["metrics"]["paid_amount"] = total
            elif status == InvoiceStatus.PENDING:
                resumo["metrics"]["pending_amount"] = total
            elif status == InvoiceStatus.CANCELED:
                resumo["metrics"]["canceled_amount"] = total
                
        return resumo