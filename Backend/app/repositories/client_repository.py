from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientFilterParams

class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: Session):
        super().__init__(Client, db)

    def get_by_cnpj(self, cnpj: str) -> Optional[Client]:
        """Busca exata por CNPJ."""
        stmt = select(Client).where(Client.cnpj == cnpj)
        return self.db.scalar(stmt)

    def create(self, client_data: ClientCreate) -> Client:
        """Adiciona um cliente à sessão; a transação é confirmada pelo service."""
        client = Client(
            company_name=client_data.company_name,
            cnpj=client_data.cnpj,
            credit_limit=client_data.credit_limit,
        )
        self.db.add(client)
        self.db.flush()
        return client

    def get_by_partial_name(self, nome: str) -> Sequence[Client]:
        """
        Busca clientes por nome parcial com desambiguação.
        O .ilike() garante que a busca seja case-insensitive.
        """
        stmt = select(Client).where(Client.company_name.ilike(f"%{nome}%"))
        return self.db.scalars(stmt).all()

    def get_filtered_clients(self, filters: ClientFilterParams) -> Sequence[Client]:
        """Busca clientes combinando os atributos informados e paginação."""
        stmt = select(Client)

        if filters.client_id is not None:
            stmt = stmt.where(Client.id == filters.client_id)
        if filters.name:
            stmt = stmt.where(Client.company_name.ilike(f"%{filters.name}%"))
        if filters.cnpj:
            stmt = stmt.where(Client.cnpj.contains(filters.cnpj))
        if filters.credit_limit is not None:
            stmt = stmt.where(Client.credit_limit == filters.credit_limit)
        if filters.min_credit_limit is not None:
            stmt = stmt.where(Client.credit_limit >= filters.min_credit_limit)
        if filters.max_credit_limit is not None:
            stmt = stmt.where(Client.credit_limit <= filters.max_credit_limit)
        if filters.status:
            stmt = stmt.where(func.upper(Client.status) == filters.status.upper())

        stmt = stmt.order_by(Client.id).offset(filters.skip).limit(filters.limit)
        return self.db.scalars(stmt).all()