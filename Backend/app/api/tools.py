# app/api/tools.py

import json
from fastapi.encoders import jsonable_encoder
from app.db.session import get_db
from app.services.credit_service import CreditService
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService
from app.services.risk_service import RiskService


def get_client_risk_analysis(client_id: int):
    """Consulta a análise de risco e perfil do cliente."""
    db = next(get_db())
    try:
        resultado = RiskService.consolidate_risk_exposure(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(resultado))
    except Exception as e:
        return json.dumps({"error": f"Erro na análise de risco: {str(e)}"})
    finally:
        db.close()


def get_client_credit_limit(client_id: int):
    """Consulta o limite de crédito disponível e utilizado do cliente."""
    db = next(get_db())
    try:
        resultado = CreditService.analyze_client_risk(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(resultado))
    except Exception as e:
        return json.dumps({"error": f"Erro ao consultar limite: {str(e)}"})
    finally:
        db.close()


def get_overdue_invoices(client_id: int):
    """Consulta faturas vencidas do cliente."""
    db = next(get_db())
    try:
        resumo = InvoiceService.list_overdue_invoices(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(resumo))
    except Exception as e:
        return json.dumps({"error": f"Erro ao consultar faturas: {str(e)}"})
    finally:
        db.close()


def get_client_orders(client_id: int):
    """Lista os pedidos históricos do cliente."""
    db = next(get_db())
    try:
        pedidos = OrderService.list_orders_by_client(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(pedidos))
    except Exception as e:
        return json.dumps({"error": f"Erro ao listar pedidos: {str(e)}"})
    finally:
        db.close()


def get_order_details(order_id: int):
    """Consulta detalhes de um pedido específico."""
    db = next(get_db())
    try:
        pedido = OrderService.get_order_details(db=db, pedido_id=order_id)
        return json.dumps(jsonable_encoder(pedido))
    except Exception as e:
        return json.dumps({"error": f"Erro na execução da ferramenta get_order_details: {str(e)}"})
    finally:
        db.close()