from sqlalchemy.orm import Session
from app.repositories.client_repository import ClientRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.client import CreditAnalyticResponse
from app.api.errors import NotFoundException

class CreditService:
    @staticmethod
    def analyze_client_risk(db: Session, client_id: int) -> CreditAnalyticResponse:
        """
        Calcula o crédito disponível, verifica bloqueios e a origem dos totais.
        Esta é a função que o Agente de IA chamará para tomar decisões financeiras.
        """
        cliente_repo = ClientRepository(db)
        fatura_repo = InvoiceRepository(db)

        # 1. Busca o cliente
        cliente = cliente_repo.get_by_id(client_id)
        if not cliente:
            raise NotFoundException(f"Cliente de ID {client_id} não encontrado no sistema.")

        # 2. Calcula a exposição (origem dos totais delegada ao banco via T022)
        exposicao = fatura_repo.calculate_client_exposure(client_id)
        
        # 3. Calcula o crédito real disponível
        credito_disponivel = cliente.credit_limit - exposicao

        # 4. Regras de Bloqueio de Negócio
        motivos_bloqueio = []
        
        if cliente.status != "ACTIVE":
            motivos_bloqueio.append(f"Cadastro bloqueado. Status atual: {cliente.status}")
            
        if credito_disponivel <= 0:
            motivos_bloqueio.append("Limite de crédito financeiro totalmente consumido.")

        is_blocked = len(motivos_bloqueio) > 0

        # 5. Retorna o contrato estrito esperado pelo schema
        return CreditAnalyticResponse(
            client_id=cliente.id,
            credit_limit=cliente.credit_limit,
            current_exposure=exposicao,
            available_credit=credito_disponivel,
            is_blocked=is_blocked,
            block_reasons=motivos_bloqueio
        )