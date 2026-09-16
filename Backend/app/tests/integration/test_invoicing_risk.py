import pytest
from datetime import date, timedelta

from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus

@pytest.fixture(autouse=True)
def setup_db(db):
    db.add(Client(
        id=1,
        cnpj="99999999999999",
        company_name="Risco LTDA",
        status="ACTIVE",
        credit_limit=10000.0,
    ))

    vencimento_passado = date.today() - timedelta(days=10)
    db.add(Invoice(
        id=1,
        client_id=1,
        amount=1500.0,
        due_date=vencimento_passado,
        status=InvoiceStatus.PENDING,
    ))

    db.commit()
    yield db


def test_rota_faturas_vencidas_200(client):
    response = client.get("/api/v1/clients/1/invoices/overdue")
    assert response.status_code == 200

    dados = response.json()
    assert dados["total_overdue_balance"] == 1500.0
    assert len(dados["overdue_invoices"]) == 1
    assert dados["overdue_invoices"][0]["days_overdue"] == 10

def test_rota_risco_integracao_completa(client):
    response = client.get("/api/v1/clients/1/risk")
    assert response.status_code == 200

    dados = response.json()
    assert dados["total_exposure"] == 1500.0
    assert dados["max_overdue_days"] == 10
    assert dados["risk_level"] == "MEDIO"

def test_rotas_erros_422_e_nao_mutacao(client, db):
    resp_422 = client.get("/api/v1/clients/invalid_text/risk")
    assert resp_422.status_code == 422

    fatura = db.query(Invoice).filter_by(id=1).first()
    assert fatura.amount == 1500.0
