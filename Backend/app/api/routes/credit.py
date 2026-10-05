from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_read_only_db
from app.db.session import get_db
from app.services.credit_service import CreditService
from app.schemas.client import (
    CreditAnalyticResponse,
    CreditLimitRequestCreate,
    CreditLimitRequestPatch,
    CreditLimitRequestResponse,
)

# Cria o roteador específico para este domínio
router = APIRouter(prefix="/clients", tags=["Crédito"])


@router.post(
    "/{id_cliente}/credit/requests",
    response_model=CreditLimitRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar revisão de limite de crédito",
    description="Registra uma solicitação pendente sem alterar o limite aprovado.",
)
def create_limit_request(
    id_cliente: int,
    payload: CreditLimitRequestCreate,
    db: Session = Depends(get_db),
) -> CreditLimitRequestResponse:
    return CreditService.create_limit_request(db, id_cliente, payload)


@router.patch(
    "/{id_cliente}/credit/requests/{request_id}",
    response_model=CreditLimitRequestResponse,
    summary="Atualizar solicitação de revisão de crédito",
    description="Atualiza campos de uma solicitação ainda pendente; não altera o limite aprovado.",
)
def update_limit_request(
    id_cliente: int,
    request_id: int,
    payload: CreditLimitRequestPatch,
    db: Session = Depends(get_db),
) -> CreditLimitRequestResponse:
    return CreditService.update_limit_request(db, id_cliente, request_id, payload)


@router.delete(
    "/{id_cliente}/credit/requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover solicitação de revisão de crédito",
    description="Remove uma solicitação pendente; não altera o limite aprovado.",
)
def delete_limit_request(
    id_cliente: int,
    request_id: int,
    db: Session = Depends(get_db),
) -> None:
    CreditService.delete_limit_request(db, id_cliente, request_id)


@router.get("/{id_cliente}/credit", response_model=CreditAnalyticResponse)
def get_analytic_credit(
    id_cliente: int,
    db: Session = Depends(get_read_only_db)
):
    """
    Retorna a análise de crédito detalhada de um cliente,
    incluindo exposição atual e status de bloqueio.
    """
    # Delega toda a complexidade para o serviço que criamos na T023
    return CreditService.analyze_client_risk(db, id_cliente)