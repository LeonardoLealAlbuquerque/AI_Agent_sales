from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientResponse
from app.services.client_service import ClientService


router = APIRouter(prefix="/clients", tags=["Clientes"])


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar cliente",
    description="Cria um cliente. O CNPJ é normalizado e deve ser único.",
)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
) -> ClientResponse:
    """Cria um registro de cliente e retorna seus dados."""
    return ClientService.create_client(db, payload)