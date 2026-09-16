import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.api.dependencies import get_read_only_db

from app.models.client import Client
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.invoice import Invoice

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """
    Fixture que cria as tabelas antes de cada teste e as destrói depois.
    Fornece a sessão do banco para os testes poderem injetar dados (seed).
    """
    Base.metadata.create_all(bind=engine)

    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """
    Fixture do TestClient que SOBRESCREVE as dependências do FastAPI.
    As rotas usam get_read_only_db; get_db também é sobrescrito por compatibilidade.
    """
    def override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_read_only_db] = override_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def db_session(db):
    """Alias para manter compatibilidade com testes antigos que usam db_session"""
    yield db
