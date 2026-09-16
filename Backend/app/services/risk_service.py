from datetime import date
from sqlalchemy.orm import Session
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.risk import RiscoConsolidado, InconsistenciaRegra

class RiskService:
    
    @staticmethod
    def _calculate_days_overdue(vencimento: date) -> int:
        hoje = date.today()
        return (hoje - vencimento).days if hoje > vencimento else 0

    @staticmethod
    def consolidate_risk_exposure(db: Session, client_id: int) -> RiscoConsolidado:
        """
        [T038] Agrega a exposição financeira do cliente, calcula o maior atraso
        e detecta inconsistências de crédito.
        """
        fatura_repo = InvoiceRepository(db)
        
        # 1. Calcular Exposição Total (Faturas pendentes)
        exposicao = fatura_repo.calculate_client_exposure(client_id)
        
        # 2. Descobrir o Maior Atraso
        faturas_vencidas = fatura_repo.get_overdue_invoices(client_id, limit=1000)
        maior_atraso = 0
        if faturas_vencidas:
            # Pega a fatura com a data de vencimento mais antiga
            fatura_mais_antiga = min(faturas_vencidas, key=lambda f: f.due_date)
            maior_atraso = RiskService._calculate_days_overdue(fatura_mais_antiga.due_date)
            
        # 3. Pedidos Abertos (Preparando a estrutura para quando houver OrderRepository)
        # TODO: Integrar com OrderRepository no futuro
        open_orders_count = 0 
        open_orders_amount = 0.0 
        
        # 4. Avaliação de Inconsistências (Motor de Regras)
        inconsistencias = []
        
        if maior_atraso > 30:
            inconsistencias.append(InconsistenciaRegra(
                rule_name="ATRASO_CRITICO",
                description=f"O cliente possui atraso máximo de {maior_atraso} dias.",
                severity="ALTA"
            ))
            
        if exposicao > 50000: # Regra de negócio de exemplo
            inconsistencias.append(InconsistenciaRegra(
                rule_name="EXPOSICAO_ELEVADA",
                description=f"Exposição financeira de R$ {exposicao:.2f} excede o limite seguro.",
                severity="MEDIA"
            ))
            
        # 5. Classificação Final do Nível de Risco
        nivel_risco = "BAIXO"
        if any(inc.severity == "ALTA" for inc in inconsistencias):
            nivel_risco = "ALTO"
        elif any(inc.severity == "MEDIA" for inc in inconsistencias) or maior_atraso > 0:
            nivel_risco = "MEDIO"
            
        return RiscoConsolidado(
            client_id=client_id,
            total_exposure=exposicao,
            max_overdue_days=maior_atraso,
            open_orders_count=open_orders_count,
            open_orders_amount=open_orders_amount,
            inconsistencies=inconsistencias,
            risk_level=nivel_risco
        )