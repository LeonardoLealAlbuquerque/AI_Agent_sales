from datetime import date
from typing import Sequence, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.invoice import Invoice, InvoiceStatus

class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    def calculate_client_exposure(self, client_id: int) -> float:
        """[T022] Mantendo a função que já existia para o CreditoService."""
        stmt = select(func.coalesce(func.sum(Invoice.amount), 0.0)).where(
            Invoice.client_id == client_id,
            Invoice.status == InvoiceStatus.PENDING
        )
        return self.db.scalar(stmt)

    def get_overdue_invoices(
        self, client_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Invoice]:
        """[T036] Retorna apenas faturas abertas com data de vencimento no passado."""
        hoje = date.today()
        stmt = (
            select(Invoice)
            .where(
                Invoice.client_id == client_id,
                Invoice.status == InvoiceStatus.PENDING,
                Invoice.due_date < hoje
            )
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def get_billing_summary_by_period(
        self, client_id: int, data_inicio: date, data_fim: date
    ) -> Sequence[Tuple[InvoiceStatus, int, float]]:
        """
        [T036] Agrega a quantidade e o valor total agrupado por status.
        O banco de dados faz a matemática pesada usando GROUP BY.
        """
        stmt = (
            select(
                Invoice.status,
                func.count(Invoice.id).label("quantidade"),
                func.sum(Invoice.amount).label("total")
            )
            .where(
                Invoice.client_id == client_id,
                Invoice.due_date >= data_inicio,
                Invoice.due_date <= data_fim
            )
            .group_by(Invoice.status)
        )
        return self.db.execute(stmt).all()