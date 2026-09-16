from datetime import date, timedelta
from app.models.client import Client
from app.models.order import Order, OrderStatus

def test_rota_obter_detalhe_pedido_200(client, db):
    cliente_teste = Client(
        company_name="Cliente Teste",
        cnpj="98765432109876",
    )
    db.add(cliente_teste)
    db.commit()

    hoje = date.today()
    pedido_teste = Order(
        client_id=cliente_teste.id,
        status=OrderStatus.PENDING,
        total_amount=100.0,
        created_at=hoje,
        estimated_delivery_date=hoje + timedelta(days=7),
    )
    db.add(pedido_teste)
    db.commit()

    response = client.get(f"/api/v1/orders/{pedido_teste.id}")
    assert response.status_code == 200
