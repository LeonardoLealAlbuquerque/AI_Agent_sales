from sqlalchemy.orm import Session
from app.repositories.client_repository import ClientRepository
from app.repositories.credit_limit_request_repository import CreditLimitRequestRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.client import (
    CreditAnalyticResponse,
    CreditLimitRequestCreate,
    CreditLimitRequestPatch,
    CreditLimitRequestResponse,
)
from app.api.errors import BusinessRuleException, NotFoundException
from sqlalchemy.exc import IntegrityError

class CreditService:
    @staticmethod
    def create_limit_request(
        db: Session, client_id: int, payload: CreditLimitRequestCreate
    ) -> CreditLimitRequestResponse:
        client = ClientRepository(db).get_by_id(client_id)
        if not client:
            raise NotFoundException(f"Cliente de ID {client_id} não encontrado no sistema.")

        repository = CreditLimitRequestRepository(db)
        try:
            request = repository.create(
                client_id=client.id,
                current_limit=client.credit_limit,
                requested_limit=payload.requested_limit,
                justification=payload.justification,
            )
            db.commit()
            db.refresh(request)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível registrar a solicitação de revisão de crédito."
            ) from exc

        return CreditLimitRequestResponse.model_validate(request)

    @staticmethod
    def update_limit_request(
        db: Session,
        client_id: int,
        request_id: int,
        payload: CreditLimitRequestPatch,
    ) -> CreditLimitRequestResponse:
        repository = CreditLimitRequestRepository(db)
        request = repository.get_for_client(request_id, client_id)
        if not request:
            raise NotFoundException("Solicitação de revisão de crédito não encontrada.")
        if request.status != "PENDING":
            raise BusinessRuleException(
                "Somente solicitações pendentes podem ser atualizadas."
            )

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(request, field_name, value)

        try:
            db.commit()
            db.refresh(request)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível atualizar a solicitação de revisão de crédito."
            ) from exc

        return CreditLimitRequestResponse.model_validate(request)

    @staticmethod
    def delete_limit_request(db: Session, client_id: int, request_id: int) -> None:
        repository = CreditLimitRequestRepository(db)
        request = repository.get_for_client(request_id, client_id)
        if not request:
            raise NotFoundException("Solicitação de revisão de crédito não encontrada.")
        if request.status != "PENDING":
            raise BusinessRuleException(
                "Somente solicitações pendentes podem ser removidas."
            )

        repository.delete(request)
        db.commit()

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