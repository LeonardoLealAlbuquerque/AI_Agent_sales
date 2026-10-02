from datetime import date
from sqlalchemy import or_, cast, String
from typing import Sequence, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.schemas.invoice import InvoiceFilterParams
from app.repositories.base import BaseRepository
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus

class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    def calculate_client_exposure(self, client_id: int) -> float:
        """[T022] Mantendo a função que já existia para o CreditoService."""
        #func.sum soma o valor de todas as faturas do cliente
        #func.coalesce retorna 0 caso não haja faturas pendentes evitando retornar NULL
        #select é usado para construir a query SQL
        #where filtra as faturas do cliente com status PENDING (pendentes)
        stmt = select(func.coalesce(func.sum(Invoice.amount), 0.0)).where(
            Invoice.client_id == client_id,
            Invoice.status == InvoiceStatus.PENDING
        )
        #self.db.scalar(stmt) executa a query no banco de dados e extrai diretamente o valor numérico resultante
        return self.db.scalar(stmt)

    def get_filtered_invoices(self, params: InvoiceFilterParams):
        query = self.db.query(Client, Invoice).join(Invoice, Client.id == Invoice.client_id)

        if params.client_id:
            query = query.filter(Client.id == params.client_id)

        if params.status:
            query = query.filter(Invoice.status == params.status)

        if params.only_overdue:
            query = query.filter(
                Invoice.status == InvoiceStatus.PENDING,
                Invoice.due_date < date.today()
            ).order_by(Invoice.due_date.asc())

        if params.min_amount is not None:
            query = query.filter(Invoice.amount >= params.min_amount)

        if params.max_amount is not None:
            query = query.filter(Invoice.amount <= params.max_amount)

        if params.payment_date_start is not None:
            query = query.filter(Invoice.payment_date >= params.payment_date_start)

        if params.payment_date_end is not None:
            query = query.filter(Invoice.payment_date <= params.payment_date_end)

        if params.search:
            words = params.search.strip().split()
            for word in words:
                term = f"%{word}%"
                query = query.filter(
                    or_(
                        Client.company_name.ilike(term),
                        Client.cnpj.ilike(term),
                        cast(Invoice.id, String).ilike(term)
                    )
                )

        return query.offset(params.skip).limit(params.limit).all()
    
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