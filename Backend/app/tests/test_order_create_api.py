from datetime import date, timedelta

from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import Order


def test_create_order_endpoint_and_openapi_schema(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [
                {
                    "product_id": 10,
                    "product_name": "Produto de Teste",
                    "quantity": 2,
                    "unit_price": 100,
                    "discount": 10,
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["client_id"] == 1
    assert response.json()["total_amount"] == 190
    assert response.json()["items"][0]["subtotal"] == 190
    assert response.json()["status"] == "PENDING"

    openapi = client.get("/openapi.json").json()
    operation = openapi["paths"]["/api/v1/orders"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/OrderCreate"
    )
    assert "201" in operation["responses"]


def test_create_order_rejects_unknown_client(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 999,
            "estimated_delivery_date": "2026-11-15",
            "items": [{"product_id": 1, "product_name": "Produto", "unit_price": 10}],
        },
    )

    assert response.status_code == 404


def test_create_order_rejects_inactive_client(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente Inativo LTDA",
        status="INACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{"product_id": 1, "product_name": "Produto", "unit_price": 10}],
        },
    )

    assert response.status_code == 400
    assert "inativo" in response.json()["detail"].lower()
    assert db.query(Order).count() == 0


def test_create_order_rejects_order_above_available_credit(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente com Limite Baixo LTDA",
        status="ACTIVE",
        credit_limit=100,
    ))
    db.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{"product_id": 1, "product_name": "Produto", "unit_price": 101}],
        },
    )

    assert response.status_code == 400
    assert "crédito insuficiente" in response.json()["detail"].lower()
    assert db.query(Order).count() == 0


def test_create_order_rejects_client_with_critical_overdue_invoice(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente Inadimplente LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.flush()
    db.add(Invoice(
        client_id=1,
        amount=1500,
        due_date=date.today() - timedelta(days=31),
        status=InvoiceStatus.PENDING,
    ))
    db.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{"product_id": 1, "product_name": "Produto", "unit_price": 10}],
        },
    )

    assert response.status_code == 400
    assert "atraso crítico" in response.json()["detail"].lower()
    assert db.query(Order).count() == 0


def test_create_order_allows_invoice_overdue_exactly_30_days(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente com Atraso Não Crítico LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.flush()
    db.add(Invoice(
        client_id=1,
        amount=1500,
        due_date=date.today() - timedelta(days=30),
        status=InvoiceStatus.PENDING,
    ))
    db.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{"product_id": 1, "product_name": "Produto", "unit_price": 10}],
        },
    )

    assert response.status_code == 201
    assert db.query(Order).count() == 1


def test_create_order_rejects_discount_above_item_total(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{
                "product_id": 1,
                "product_name": "Produto",
                "quantity": 2,
                "unit_price": 10,
                "discount": 25,
            }],
        },
    )

    assert response.status_code == 422


def test_post_and_patch_order_items_recalculate_order_total(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    order_response = client.post(
        "/api/v1/orders",
        json={
            "client_id": 1,
            "estimated_delivery_date": "2026-11-15",
            "items": [{
                "product_id": 1,
                "product_name": "Item Inicial",
                "quantity": 1,
                "unit_price": 10,
            }],
        },
    )
    order_id = order_response.json()["id"]

    item_response = client.post(
        f"/api/v1/orders/{order_id}/items",
        json={
            "product_id": 2,
            "product_name": "Item Adicional",
            "quantity": 2,
            "unit_price": 10,
            "discount": 4,
        },
    )
    assert item_response.status_code == 201
    assert item_response.json()["subtotal"] == 16

    item_id = item_response.json()["id"]
    patch_response = client.patch(
        f"/api/v1/orders/{order_id}/items/{item_id}",
        json={"unit_price": 12},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["subtotal"] == 20

    detail_response = client.get(f"/api/v1/orders/{order_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["total_amount"] == 30
    assert len(detail_response.json()["items"]) == 2

    deleted = client.delete(f"/api/v1/orders/{order_id}/items/{item_id}")
    assert deleted.status_code == 204

    detail_after_delete = client.get(f"/api/v1/orders/{order_id}")
    assert detail_after_delete.json()["total_amount"] == 10
    assert len(detail_after_delete.json()["items"]) == 1

    deleting_last_item = client.delete(
        f"/api/v1/orders/{order_id}/items/{detail_after_delete.json()['items'][0]['id']}"
    )
    assert deleting_last_item.status_code == 400

    openapi = client.get("/openapi.json").json()
    assert "post" in openapi["paths"]["/api/v1/orders/{order_id}/items"]
    assert "patch" in openapi["paths"]["/api/v1/orders/{order_id}/items/{item_id}"]
    assert "delete" in openapi["paths"]["/api/v1/orders/{order_id}/items/{item_id}"]