# app/api/tools.py

import json
from datetime import date
from typing import Optional
from fastapi.encoders import jsonable_encoder
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import InvoiceFilterParams
from app.schemas.client import ClientFilterParams
from app.db.session import get_db
from app.repositories.client_repository import ClientRepository
from app.services.credit_service import CreditService
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService
from app.services.risk_service import RiskService


def _resolve_client_id(db, client_id: Optional[int], name: Optional[str]) -> int:
    """Resolve um cliente por ID ou nome parcial, rejeitando resultados ambíguos."""
    if client_id is not None:
        return client_id
    if not name or not name.strip():
        raise ValueError("Informe client_id ou name para identificar o cliente.")

    matches = ClientRepository(db).get_by_partial_name(name.strip())
    if not matches:
        raise ValueError(f"Nenhum cliente encontrado para o nome '{name}'.")
    if len(matches) > 1:
        names = ", ".join(cliente.company_name for cliente in matches[:5])
        raise ValueError(f"Nome de cliente ambíguo. Clientes encontrados: {names}.")
    return matches[0].id


def get_client_risk_analysis(client_id: Optional[int] = None, name: Optional[str] = None):
    """Consulta a análise de risco e perfil do cliente."""
    db = next(get_db())
    try:
        client_id = _resolve_client_id(db, client_id, name)
        resultado = RiskService.consolidate_risk_exposure(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(resultado))
    except Exception as e:
        return json.dumps({"error": f"Erro na análise de risco: {str(e)}"})
    finally:
        db.close()


def get_client_credit_limit(client_id: Optional[int] = None, name: Optional[str] = None):
    """Consulta o limite de crédito disponível e utilizado do cliente."""
    db = next(get_db())
    try:
        client_id = _resolve_client_id(db, client_id, name)
        resultado = CreditService.analyze_client_risk(db=db, client_id=client_id)
        return json.dumps(jsonable_encoder(resultado))
    except Exception as e:
        return json.dumps({"error": f"Erro ao consultar limite: {str(e)}"})
    finally:
        db.close()


def get_overdue_invoices(client_id: Optional[int] = None, name: Optional[str] = None):
    """Consulta faturas vencidas do cliente."""
    db = next(get_db())
    try:
        client_id = _resolve_client_id(db, client_id, name)
        filters = InvoiceFilterParams(client_id=client_id, only_overdue=True)
        resumo = InvoiceService.list_invoices(db=db, filters=filters)
        return json.dumps(jsonable_encoder(resumo))
    except Exception as e:
        return json.dumps({"error": f"Erro ao consultar faturas: {str(e)}"})
    finally:
        db.close()


def get_client_orders(client_id: Optional[int] = None, name: Optional[str] = None):
    """Lista os pedidos históricos do cliente."""
    db = next(get_db())
    try:
        client_id = _resolve_client_id(db, client_id, name)
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


def list_invoices(
    search: Optional[str] = None,
    client_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    only_overdue: bool = False,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    payment_date_start: Optional[date] = None,
    payment_date_end: Optional[date] = None,
    limit: int = 50, 
    skip: int = 0
):
    """Lista faturas abertas de todos os clientes, sem exigir client_id."""
    db = next(get_db())
    try:
        filters = InvoiceFilterParams(
            search=search,
            client_id=client_id,
            status=status,
            only_overdue=only_overdue,
            min_amount=min_amount,
            max_amount=max_amount,
            payment_date_start=payment_date_start,
            payment_date_end=payment_date_end,
            skip=skip,
            limit=limit,
        )
        resultado = InvoiceService.list_invoices(db=db, filters=filters)
        return json.dumps(jsonable_encoder(resultado))
    except Exception as e:
        return json.dumps({"error": f"Erro ao listar faturas abertas: {str(e)}"})
    finally:
        db.close()


def list_clients(
    client_id: Optional[int] = None,
    name: Optional[str] = None,
    cnpj: Optional[str] = None,
    credit_limit: Optional[float] = None,
    min_credit_limit: Optional[float] = None,
    max_credit_limit: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    """Lista clientes aplicando filtros combináveis e paginação.

    Filtros: ID exato, nome parcial, CNPJ completo ou parcial, limite exato ou
    intervalo de limite, e status. Retorna os cadastros correspondentes sem
    executar consultas de risco/crédito; use o ID retornado para isso.
    """
    db = next(get_db())
    try:
        filters = ClientFilterParams(
            client_id=client_id,
            name=name,
            cnpj=cnpj,
            credit_limit=credit_limit,
            min_credit_limit=min_credit_limit,
            max_credit_limit=max_credit_limit,
            status=status,
            limit=limit,
            skip=skip,
        )
        clients = ClientRepository(db).get_filtered_clients(filters)
        result = {"total_clients": len(clients), "clients": clients}
        return json.dumps(jsonable_encoder(result))
    except Exception as e:
        return json.dumps({"error": f"Erro ao listar clientes: {str(e)}"})
    finally:
        db.close()