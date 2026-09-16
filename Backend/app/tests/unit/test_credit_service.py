import pytest
from unittest.mock import MagicMock, patch
from app.services.credit_service import CreditService
from app.api.errors import NotFoundException
from app.models.client import Client

# O @patch substitui temporariamente a classe real por um "dublê" (mock)
@patch("app.services.credit_service.ClientRepository")
@patch("app.services.credit_service.InvoiceRepository")
def test_analise_credito_com_exposicao_sucesso(mock_fatura_repo, mock_cliente_repo):
    # 1. Configuração (Given)
    mock_db = MagicMock()
    cliente_mock = Client(id=1, credit_limit=10000.0, status="ACTIVE")
    
    # Ensinamos o mock a devolver nosso cliente fictício e uma exposição de 3000
    mock_cliente_repo.return_value.get_by_id.return_value = cliente_mock
    mock_fatura_repo.return_value.calculate_client_exposure.return_value = 3000.0

    # 2. Execução (When)
    resultado = CreditService.analyze_client_risk(mock_db, 1)

    # 3. Verificação (Then)
    assert resultado.client_id == 1
    assert resultado.available_credit == 7000.0 # 10000 - 3000
    assert resultado.is_blocked is False
    assert len(resultado.block_reasons) == 0

@patch("app.services.credit_service.ClientRepository")
@patch("app.services.credit_service.InvoiceRepository")
def test_analise_credito_limite_excedido_bloqueia_cliente(mock_fatura_repo, mock_cliente_repo):
    mock_db = MagicMock()
    cliente_mock = Client(id=2, credit_limit=5000.0, status="ACTIVE")
    
    mock_cliente_repo.return_value.get_by_id.return_value = cliente_mock
    mock_fatura_repo.return_value.calculate_client_exposure.return_value = 6000.0

    resultado = CreditService.analyze_client_risk(mock_db, 2)

    assert resultado.available_credit == -1000.0
    assert resultado.is_blocked is True
    assert "Limite de crédito financeiro totalmente consumido." in resultado.block_reasons

@patch("app.services.credit_service.ClientRepository")
@patch("app.services.credit_service.InvoiceRepository")
def test_analise_credito_cliente_inativo_bloqueado(mock_fatura_repo, mock_cliente_repo):
    mock_db = MagicMock()
    cliente_mock = Client(id=3, credit_limit=10000.0, status="INACTIVE")
    
    mock_cliente_repo.return_value.get_by_id.return_value = cliente_mock
    mock_fatura_repo.return_value.calculate_client_exposure.return_value = 0.0

    resultado = CreditService.analyze_client_risk(mock_db, 3)

    assert resultado.is_blocked is True
    assert "Cadastro bloqueado. Status atual: INACTIVE" in resultado.block_reasons

@patch("app.services.credit_service.ClientRepository")
def test_analise_credito_cliente_nao_encontrado(mock_cliente_repo):
    mock_db = MagicMock()
    mock_cliente_repo.return_value.get_by_id.return_value = None

    # Verifica se a exceção de domínio correta é lançada
    with pytest.raises(NotFoundException) as exc_info:
        CreditService.analyze_client_risk(mock_db, 999)
        
    assert "não encontrado" in exc_info.value.message