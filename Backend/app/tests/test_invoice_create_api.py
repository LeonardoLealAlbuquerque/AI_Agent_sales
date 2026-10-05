from datetime import date

from app.models.client import Client


def test_create_invoice_endpoint_and_openapi_schema(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    response = client.post(
        "/api/v1/invoices",
        json={"client_id": 1, "amount": 1500, "due_date": "2026-11-15"},
    )

    assert response.status_code == 201
    assert response.json()["client_id"] == 1
    assert response.json()["amount"] == 1500
    assert response.json()["due_date"] == "2026-11-15"
    assert response.json()["status"] == "PENDING"

    openapi = client.get("/openapi.json").json()
    operation = openapi["paths"]["/api/v1/invoices"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/InvoiceCreate"
    )
    assert "201" in operation["responses"]


def test_create_invoice_rejects_unknown_client(client):
    response = client.post(
        "/api/v1/invoices",
        json={"client_id": 999, "amount": 1500, "due_date": date.today().isoformat()},
    )

    assert response.status_code == 404


def test_create_invoice_rejects_non_positive_amount(client):
    response = client.post(
        "/api/v1/invoices",
        json={"client_id": 1, "amount": 0, "due_date": date.today().isoformat()},
    )

    assert response.status_code == 422