import json
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


def test_rota_lista_faturas_abertas_de_todos_os_clientes(client, db):
    segundo_cliente = Client(
        id=2,
        cnpj="88888888888888",
        company_name="Outro Cliente LTDA",
        status="ACTIVE",
        credit_limit=5000.0,
    )
    db.add(segundo_cliente)
    db.add(Invoice(
        id=2,
        client_id=2,
        amount=800.0,
        due_date=date.today() + timedelta(days=5),
        status=InvoiceStatus.PENDING,
    ))
    db.commit()

    response = client.get("/api/v1/invoices/open")

    assert response.status_code == 200
    dados = response.json()
    assert dados["total_clients"] == 2
    assert dados["total_open_invoices"] == 2
    assert {item["client_name"] for item in dados["clients"]} == {
        "Risco LTDA",
        "Outro Cliente LTDA",
    }


def test_rota_busca_faturas_por_nome_parcial_da_empresa(client, db):
    db.add(Client(
        id=2,
        cnpj="88888888888888",
        company_name="TechCorp Ltda.",
        status="ACTIVE",
        credit_limit=5000.0,
    ))
    db.add(Invoice(
        id=2,
        client_id=2,
        amount=1200.0,
        due_date=date.today() + timedelta(days=10),
        status=InvoiceStatus.PENDING,
    ))
    db.commit()

    response = client.get("/api/v1/invoices/invoices", params={"search": "TechCorp"})

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices_count"] == 1
    assert data["clients"][0]["client_name"] == "TechCorp Ltda."


def test_rota_lista_faturas_combina_filtros(client, db):
    db.add_all([
        Invoice(
            id=2,
            client_id=1,
            amount=2500.0,
            due_date=date(2026, 2, 1),
            payment_date=date(2026, 2, 10),
            status=InvoiceStatus.PAID,
        ),
        Invoice(
            id=3,
            client_id=1,
            amount=3500.0,
            due_date=date(2026, 2, 1),
            payment_date=date(2026, 2, 10),
            status=InvoiceStatus.PAID,
        ),
        Invoice(
            id=4,
            client_id=1,
            amount=2500.0,
            due_date=date(2026, 2, 1),
            payment_date=date(2026, 3, 10),
            status=InvoiceStatus.PAID,
        ),
    ])
    db.commit()

    response = client.get(
        "/api/v1/invoices/invoices",
        params={
            "status": "PAID",
            "min_amount": 2000,
            "max_amount": 3000,
            "payment_date_start": "2026-02-01",
            "payment_date_end": "2026-02-28",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices_count"] == 1
    assert data["clients"][0]["invoices"][0]["id"] == 2


def test_tool_agente_lista_faturas_com_filtros(db, monkeypatch):
    from app import api
    from app.agent.tools import GROQ_TOOL_SCHEMAS, execute_tool

    db.add(Invoice(
        id=2,
        client_id=1,
        amount=2500.0,
        due_date=date(2026, 2, 1),
        payment_date=date(2026, 2, 10),
        status=InvoiceStatus.PAID,
    ))
    db.commit()
    monkeypatch.setattr(api.tools, "get_db", lambda: iter([db]))

    invoice_tool = next(
        tool["function"] for tool in GROQ_TOOL_SCHEMAS
        if tool["function"]["name"] == "list_invoices"
    )
    assert {
        "min_amount",
        "max_amount",
        "payment_date_start",
        "payment_date_end",
    }.issubset(invoice_tool["parameters"]["properties"])

    result = json.loads(execute_tool("list_invoices", {
        "status": "PAID",
        "min_amount": 2000,
        "max_amount": 3000,
        "payment_date_start": "2026-02-01",
        "payment_date_end": "2026-02-28",
    }))

    assert result["total_invoices_count"] == 1
    assert result["clients"][0]["invoices"][0]["id"] == 2


def test_tool_agente_busca_faturas_por_nome_parcial(db, monkeypatch):
    from app import api
    from app.agent.tools import execute_tool

    db.add(Client(
        id=2,
        cnpj="88888888888888",
        company_name="TechCorp Ltda.",
        status="ACTIVE",
        credit_limit=5000.0,
    ))
    db.add(Invoice(
        id=2,
        client_id=2,
        amount=1200.0,
        due_date=date.today() + timedelta(days=10),
        status=InvoiceStatus.PENDING,
    ))
    db.commit()
    monkeypatch.setattr(api.tools, "get_db", lambda: iter([db]))

    result = json.loads(execute_tool("list_invoices", {"search": "TechCorp"}))

    assert result["total_invoices_count"] == 1
    assert result["clients"][0]["client_name"] == "TechCorp Ltda."
    assert result["clients"][0]["invoices"][0]["id"] == 2


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
