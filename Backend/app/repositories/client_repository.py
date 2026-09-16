from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.client import Client

class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: Session):
        super().__init__(Client, db)

    def get_by_cnpj(self, cnpj: str) -> Optional[Client]:
        """Busca exata por CNPJ."""
        stmt = select(Client).where(Client.cnpj == cnpj)
        return self.db.scalar(stmt)

    def get_by_partial_name(self, nome: str) -> Sequence[Client]:
        """
        Busca clientes por nome parcial com desambiguação.
        O .ilike() garante que a busca seja case-insensitive.
        """
        stmt = select(Client).where(Client.company_name.ilike(f"%{nome}%"))
        return self.db.scalars(stmt).all()