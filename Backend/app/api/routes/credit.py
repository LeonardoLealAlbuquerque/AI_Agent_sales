from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_read_only_db
from app.services.credit_service import CreditService
from app.schemas.client import CreditAnalyticResponse

# Cria o roteador específico para este domínio
router = APIRouter(prefix="/clients", tags=["Crédito"])

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