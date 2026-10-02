from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import BusinessRuleException
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientResponse


class ClientService:
    @staticmethod
    def create_client(db: Session, client_data: ClientCreate) -> ClientResponse:
        """Valida regras de cadastro, persiste o cliente e monta a resposta da API."""
        repository = ClientRepository(db)

        if repository.get_by_cnpj(client_data.cnpj):
            raise BusinessRuleException("Já existe um cliente cadastrado com este CNPJ.")

        try:
            client = repository.create(client_data)
            db.commit()
            db.refresh(client)
        except IntegrityError as exc:
            db.rollback()
            raise BusinessRuleException(
                "Não foi possível cadastrar o cliente. Verifique se o CNPJ já está cadastrado."
            ) from exc

        return ClientResponse.model_validate(client)