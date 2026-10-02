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
    hoje = date.today()
    assert InvoiceService._calculate_days_overdue(hoje) == 0

def test_calculo_atraso_vencimento_passado():
    cinco_dias_atras = date.today() - timedelta(days=5)
    assert InvoiceService._calculate_days_overdue(cinco_dias_atras) == 5

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
def test_consolidar_risco_gera_inconsistencias(mock_list_invoices, mock_invoice_repo):
    mock_db = MagicMock()
    
    # 1. Simula uma exposição absurdamente alta (> 50.000)
    mock_invoice_repo.return_value.calculate_client_exposure.return_value = 60000.0
    
    # 2. Simula uma fatura vencida há 40 dias (gera atraso crítico > 30)
    mock_list_invoices.return_value = {
        "clients": [{"invoices": [{"days_overdue": 40}]}],
    }
    risco = RiskService.consolidate_risk_exposure(mock_db, client_id=1)
    
    assert risco.total_exposure == 60000.0
    assert risco.max_overdue_days == 40
    assert risco.risk_level == "ALTO"
    
    regras_acionadas = [inc.rule_name for inc in risco.inconsistencies]
    assert "ATRASO_CRITICO" in regras_acionadas
    assert "EXPOSICAO_ELEVADA" in regras_acionadas
    mock_list_invoices.assert_called_once()
    db_argument, filters = mock_list_invoices.call_args.args
    assert db_argument is mock_db
    assert filters == InvoiceFilterParams(client_id=1, only_overdue=True, limit=100)