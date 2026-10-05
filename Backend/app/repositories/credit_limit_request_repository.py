from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit_limit_request import CreditLimitRequest
from app.repositories.base import BaseRepository


class CreditLimitRequestRepository(BaseRepository[CreditLimitRequest]):
    def __init__(self, db: Session):
        super().__init__(CreditLimitRequest, db)

    def get_for_client(
        self, request_id: int, client_id: int
    ) -> Optional[CreditLimitRequest]:
        stmt = select(CreditLimitRequest).where(
            CreditLimitRequest.id == request_id,
            CreditLimitRequest.client_id == client_id,
        )
        return self.db.scalar(stmt)

    def create(
        self,
        client_id: int,
        current_limit: float,
        requested_limit: float,
        justification: str,
    ) -> CreditLimitRequest:
        request = CreditLimitRequest(
            client_id=client_id,
            current_limit=current_limit,
            requested_limit=requested_limit,
            justification=justification,
        )
        self.db.add(request)
        self.db.flush()
        return request

    def delete(self, request: CreditLimitRequest) -> None:
        self.db.delete(request)