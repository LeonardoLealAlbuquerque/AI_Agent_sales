import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from app.services.order_service import OrderService
from app.api.errors import NotFoundException
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

def test_calculo_logistica_entregue_no_prazo():
    previsao = date(2026, 10, 10)
    entrega_real = date(2026, 10, 9)
    
    info = OrderService._calculate_logistics(previsao, entrega_real)
    
    assert info.is_delayed is False
    assert info.delay_days == 0
    assert info.actual_delivery_date == entrega_real

def test_calculo_logistica_entregue_com_atraso():
    previsao = date(2026, 10, 10)
    entrega_real = date(2026, 10, 15)
    
    info = OrderService._calculate_logistics(previsao, entrega_real)
    
    assert info.is_delayed is True
    assert info.delay_days == 5

def test_calculo_logistica_pendente_e_atrasado():
    # Simulando que hoje é dia 20, mas a previsão era dia 10
    hoje = date.today()
    previsao = hoje - timedelta(days=10) 
    
    info = OrderService._calculate_logistics(previsao, None)
    
    assert info.is_delayed is True
    assert info.delay_days == 10
    assert info.actual_delivery_date is None

@patch("app.services.order_service.OrderRepository")
def test_obter_detalhes_pedido_sucesso(mock_order_repo):
    mock_db = MagicMock()
    
    # Montando um pedido dublê com itens
    item_mock = OrderItem(
        id=1,
        order_id=1,
        product_id=101,
        product_name="Servidor Rack",  # <-- Mude de "Produto Teste" para "Servidor Rack"
        quantity=2,
        unit_price=5000.0,
        subtotal=10000.0
    )
    pedido_mock = Order(
        id=100, 
        client_id=1, 
        status=OrderStatus.DELIVERED,
        created_at=date(2026, 1, 1),
        estimated_delivery_date=date(2026, 1, 10),
        delivery_date=date(2026, 1, 9),
        total_amount=10000.0
    )
    # O SQLAlchemy usa a relação de itens, então simulamos isso no mock
    pedido_mock.items = [item_mock] 
    
    mock_order_repo.return_value.obter_detalhes_pedido.return_value = pedido_mock
    
    resultado = OrderService.get_order_details(mock_db, 100)
    
    assert resultado.id == 100
    assert resultado.total_amount == 10000.0
    assert len(resultado.items) == 1
    assert resultado.items[0].product_name == "Servidor Rack"
    assert resultado.delivery_info.is_delayed is False

@patch("app.services.order_service.OrderRepository")
def test_obter_detalhes_pedido_inexistente(mock_order_repo):
    mock_db = MagicMock()
    mock_order_repo.return_value.obter_detalhes_pedido.return_value = None
    
    with pytest.raises(NotFoundException):
        OrderService.get_order_details(mock_db, 999)