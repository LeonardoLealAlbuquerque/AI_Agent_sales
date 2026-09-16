from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_read_only_db
from app.services.order_service import OrderService
from app.schemas.order import OrderSummary, OrderDetail

# Novo router específico para Pedidos
router = APIRouter(prefix="/orders", tags=["Pedidos"])
router_clientes = APIRouter(prefix="/clients", tags=["Clientes (Pedidos)"])

@router_clientes.get("/{client_id}/orders", response_model=List[OrderSummary])
def client_orders_list(
    client_id: int,
    skip: int = Query(0, ge=0, description="Pular X registros"),
    limit: int = Query(100, le=1000, description="Máximo de registros"),
    db: Session = Depends(get_read_only_db)
):
    """Retorna o histórico de pedidos de um cliente (sem os itens)."""
    return OrderService.list_orders_by_client(db, client_id, skip, limit)


@router.get("/{pedido_id}", response_model=OrderDetail)
def get_order(
    pedido_id: int,
    db: Session = Depends(get_read_only_db)
):
    """Retorna a visão detalhada de um pedido, incluindo seus itens."""
    return OrderService.get_order_details(db, pedido_id)
