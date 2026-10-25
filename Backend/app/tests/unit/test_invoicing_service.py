import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from app.services.invoice_service import InvoiceService
from app.services.risk_service import RiskService
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import InvoiceFilterParams

# ==========================================
# Testes de Tempo e Atraso (FaturaService)
# ==========================================
def test_calculo_atraso_vencimento_hoje_retorna_zero():
    data_referencia = date(2026, 10, 24)
    assert InvoiceService._calculate_days_overdue(
        data_referencia, reference_date=data_referencia
    ) == 0

def test_calculo_atraso_vencimento_passado():
    data_referencia = date(2026, 10, 24)
    cinco_dias_atras = data_referencia - timedelta(days=5)
    assert InvoiceService._calculate_days_overdue(
        cinco_dias_atras, reference_date=data_referencia
    ) == 5

@patch("app.services.invoice_service.InvoiceRepository")
def test_resumo_financeiro_pagamento_e_cancelamento(mock_fatura_repo):
    mock_db = MagicMock()
    
    # Simulando o retorno do banco: (Status, Quantidade, Valor Total)
    mock_fatura_repo.return_value.get_billing_summary_by_period.return_value = [
        (InvoiceStatus.PAID, 2, 2000.0),
        (InvoiceStatus.CANCELED, 1, 500.0)
    ]
    
    resumo = InvoiceService.generate_financial_summary(
        mock_db, client_id=1, data_inicio=date(2026, 1, 1), data_fim=date(2026, 1, 31)
    )
    
    assert resumo["metrics"]["paid_amount"] == 2000.0
    assert resumo["metrics"]["canceled_amount"] == 500.0
    assert resumo["metrics"]["pending_amount"] == 0.0 # Não veio do banco, deve ser 0
    assert resumo["metrics"]["total_invoices_count"] == 3

# ==========================================
# Testes de Inconsistências (RiskService)
# ==========================================
@patch("app.services.risk_service.InvoiceRepository")
@patch("app.services.risk_service.InvoiceService.list_invoices")
@patch("app.services.risk_service.OrderRepository")
@patch("app.services.risk_service.ClientRepository")
def test_consolidar_risco_gera_inconsistencias(
    mock_client_repo,
    mock_order_repo,
    mock_list_invoices,
    mock_invoice_repo,
):
    mock_db = MagicMock()
    mock_client_repo.return_value.get_by_id.return_value = MagicMock(
        credit_limit=50000.0
    )
    
    # 1. Simula exposição acima do limite aprovado do cliente
    mock_invoice_repo.return_value.calculate_client_exposure.return_value = 60000.0
    mock_order_repo.return_value.calculate_open_order_summary.return_value = (2, 3500.0)
    
    # 2. Simula uma fatura vencida há 40 dias (gera atraso crítico > 30)
    mock_list_invoices.return_value = {
        "clients": [{"invoices": [{"days_overdue": 40}]}],
    }
    risco = RiskService.consolidate_risk_exposure(mock_db, client_id=1)
    
    assert risco.total_exposure == 60000.0
    assert risco.max_overdue_days == 40
    assert risco.open_orders_count == 2
    assert risco.open_orders_amount == 3500.0
    assert risco.risk_level == "ALTO"
    
    regras_acionadas = [inc.rule_name for inc in risco.inconsistencies]
    assert "ATRASO_CRITICO" in regras_acionadas
    assert "EXPOSICAO_ELEVADA" in regras_acionadas
    mock_list_invoices.assert_called_once()
    db_argument, filters = mock_list_invoices.call_args.args
    assert db_argument is mock_db
    assert filters == InvoiceFilterParams(client_id=1, only_overdue=True, limit=100)
    assert mock_list_invoices.call_args.kwargs["reference_date"] == date.today()
    mock_order_repo.return_value.calculate_open_order_summary.assert_called_once_with(1)


@patch("app.services.risk_service.InvoiceRepository")
@patch("app.services.risk_service.InvoiceService.list_invoices")
@patch("app.services.risk_service.OrderRepository")
@patch("app.services.risk_service.ClientRepository")
def test_exposicao_acima_do_limite_individual_gera_inconsistencia(
    mock_client_repo,
    mock_order_repo,
    mock_list_invoices,
    mock_invoice_repo,
):
    mock_client_repo.return_value.get_by_id.return_value = MagicMock(
        credit_limit=10000.0
    )
    mock_invoice_repo.return_value.calculate_client_exposure.return_value = 12000.0
    mock_list_invoices.return_value = {"clients": []}
    mock_order_repo.return_value.calculate_open_order_summary.return_value = (0, 0.0)

    risco = RiskService.consolidate_risk_exposure(MagicMock(), client_id=1)

    assert risco.risk_level == "MEDIO"
    exposicao_elevada = next(
        inconsistency
        for inconsistency in risco.inconsistencies
        if inconsistency.rule_name == "EXPOSICAO_ELEVADA"
    )
    assert "R$ 10000.00" in exposicao_elevada.description


@patch("app.services.risk_service.InvoiceRepository")
@patch("app.services.risk_service.InvoiceService.list_invoices")
@patch("app.services.risk_service.OrderRepository")
@patch("app.services.risk_service.ClientRepository")
def test_exposicao_igual_ao_limite_nao_gera_inconsistencia(
    mock_client_repo,
    mock_order_repo,
    mock_list_invoices,
    mock_invoice_repo,
):
    mock_client_repo.return_value.get_by_id.return_value = MagicMock(
        credit_limit=12000.0
    )
    mock_invoice_repo.return_value.calculate_client_exposure.return_value = 12000.0
    mock_list_invoices.return_value = {"clients": []}
    mock_order_repo.return_value.calculate_open_order_summary.return_value = (0, 0.0)

    risco = RiskService.consolidate_risk_exposure(MagicMock(), client_id=1)

    assert "EXPOSICAO_ELEVADA" not in [
        inconsistency.rule_name for inconsistency in risco.inconsistencies
    ]
    assert risco.risk_level == "BAIXO"


@patch("app.services.risk_service.ClientRepository")
def test_consolidar_risco_rejeita_cliente_inexistente(mock_client_repo):
    from app.api.errors import NotFoundException

    mock_client_repo.return_value.get_by_id.return_value = None

    with pytest.raises(NotFoundException, match="Cliente de ID 123 não encontrado"):
        RiskService.consolidate_risk_exposure(MagicMock(), client_id=123)