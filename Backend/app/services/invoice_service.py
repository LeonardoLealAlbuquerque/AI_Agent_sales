from datetime import date
from sqlalchemy.orm import Session
from app.repositories.invoice_repository import InvoiceRepository
from app.models.invoice import InvoiceStatus

class InvoiceService:
    
    @staticmethod
    def _calculate_days_overdue(vencimento: date) -> int:
        """Calcula dias corridos de atraso em relação à data atual."""
        hoje = date.today()
        if hoje > vencimento:
            return (hoje - vencimento).days
        return 0

    @staticmethod
    def list_overdue_invoices(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> dict:
        """
        [T037] Busca faturas vencidas e calcula os estados derivados 
        (dias de atraso e o saldo total devedor dessa listagem).
        """
        repo = InvoiceRepository(db)
        faturas_db = repo.get_overdue_invoices(client_id, skip, limit)
        
        faturas_processadas = []
        saldo_vencido_total = 0.0
        
        for f in faturas_db:
            atraso = InvoiceService._calculate_days_overdue(f.due_date)
            saldo_vencido_total += f.amount
            
            faturas_processadas.append({
                "id": f.id,
                "amount": f.amount,
                "due_date": f.due_date,
                "days_overdue": atraso,
                "critical_status": atraso > 30 # Derivação de regra de negócio (ex: mais de 30 dias é crítico)
            })
            
        return {
            "client_id": client_id,
            "total_overdue_balance": saldo_vencido_total,
            "overdue_invoices": faturas_processadas
        }

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