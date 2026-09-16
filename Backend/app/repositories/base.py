from typing import Generic, TypeVar, Type, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    def get_by_id(self, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        return self.db.scalar(stmt)
    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()