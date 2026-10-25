from datetime import date
from sqlalchemy.orm import Session
from app.api.errors import NotFoundException
from app.repositories.client_repository import ClientRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.invoice import InvoiceFilterParams
from app.schemas.risk import ConsolidatedRisk, RuleInconsistency
from app.services.invoice_service import InvoiceService

class RiskService:

    @staticmethod
    def consolidate_risk_exposure(db: Session, client_id: int) -> ConsolidatedRisk:
        """
        [T038] Agrega a exposição financeira do cliente, calcula o maior atraso
        e detecta inconsistências de crédito.
        """
        client = ClientRepository(db).get_by_id(client_id)
        if not client:
            raise NotFoundException(
                f"Cliente de ID {client_id} não encontrado no sistema."
            )

        fatura_repo = InvoiceRepository(db)
        
        # 1. Calcular Exposição Total (Faturas pendentes)
        exposicao = fatura_repo.calculate_client_exposure(client_id)
        
        # 2. Descobrir o Maior Atraso
        reference_date = date.today()
        faturas_vencidas = InvoiceService.list_invoices(
            db,
            InvoiceFilterParams(client_id=client_id, only_overdue=True, limit=100),
            reference_date=reference_date,
        )
        maior_atraso = max(
            (
                invoice["days_overdue"]
                for client in faturas_vencidas["clients"]
                for invoice in client["invoices"]
            ),
            default=0,
        )

        # 3. Pedidos pendentes ou enviados ainda representam compromissos em aberto.
        open_orders_count, open_orders_amount = OrderRepository(
            db
        ).calculate_open_order_summary(client_id)
        
        # 4. Avaliação de Inconsistências (Motor de Regras)
        inconsistencias = []
        
        if maior_atraso > 30:
            inconsistencias.append(RuleInconsistency(
                rule_name="ATRASO_CRITICO",
                description=f"O cliente possui atraso máximo de {maior_atraso} dias.",
                severity="ALTA"
            ))
            
        if exposicao > client.credit_limit:
            inconsistencias.append(RuleInconsistency(
                rule_name="EXPOSICAO_ELEVADA",
                description=(
                    f"Exposição financeira de R$ {exposicao:.2f} excede "
                    f"o limite de crédito aprovado de R$ {client.credit_limit:.2f}."
                ),
                severity="MEDIA"
            ))
            
        # 5. Classificação Final do Nível de Risco
        nivel_risco = "BAIXO"
        if any(inc.severity == "ALTA" for inc in inconsistencias):
            nivel_risco = "ALTO"
        elif any(inc.severity == "MEDIA" for inc in inconsistencias) or maior_atraso > 0:
            nivel_risco = "MEDIO"
            
        return ConsolidatedRisk(
            client_id=client_id,
            total_exposure=exposicao,
            max_overdue_days=maior_atraso,
            open_orders_count=open_orders_count,
            open_orders_amount=open_orders_amount,
            inconsistencies=inconsistencias,
            risk_level=nivel_risco
        )