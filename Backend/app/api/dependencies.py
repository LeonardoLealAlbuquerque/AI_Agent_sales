from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

def get_read_only_db() -> Generator[Session, None, None]:
    """
    Injeta uma sessão do banco dedicada a operações de leitura (rotas GET).
    Garante que a sessão será fechada sem realizar commits (rollback automático).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()