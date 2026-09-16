from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_read_only_db
from app.services.risk_service import RiskService
from app.schemas.risk import RiscoConsolidado

router = APIRouter(prefix="/clients/{client_id}/risk", tags=["Risco e Crédito"])

@router.get("", response_model=RiscoConsolidado)
def get_consolidated_risk(
    client_id: int,
    db: Session = Depends(get_read_only_db)
):
    """Motor de regras: cruza exposição financeira e atrasos para determinar o risco."""
    return RiskService.consolidate_risk_exposure(db, client_id)