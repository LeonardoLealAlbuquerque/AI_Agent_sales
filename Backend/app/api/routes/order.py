from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_read_only_db
from app.db.session import get_db
from app.services.order_service import OrderService
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemPatch,
    OrderItemResponse,
    OrderSummary,
    OrderDetail,
)

# Novo router específico para Pedidos
router = APIRouter(prefix="/orders", tags=["Pedidos"])
router_clientes = APIRouter(prefix="/clients", tags=["Clientes (Pedidos)"])


@router.post(
    "",
    response_model=OrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar pedido",
    description="Cria um pedido para um cliente existente, incluindo seus itens.",
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderDetail:
    """Cria um pedido e retorna os dados do pedido e seus itens."""
    return OrderService.create_order(db, payload)


@router.post(
    "/{order_id}/items",
    response_model=OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item ao pedido",
)
def create_order_item(
    order_id: int,
    payload: OrderItemCreate,
    db: Session = Depends(get_db),
) -> OrderItemResponse:
    return OrderService.create_order_item(db, order_id, payload)


@router.patch(
    "/{order_id}/items/{item_id}",
    response_model=OrderItemResponse,
    summary="Atualizar item do pedido",
)
def update_order_item(
    order_id: int,
    item_id: int,
    payload: OrderItemPatch,
    db: Session = Depends(get_db),
) -> OrderItemResponse:
    return OrderService.update_order_item(db, order_id, item_id, payload)


@router.delete(
    "/{order_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover item do pedido",
    description="Remove um item e recalcula o total; o pedido deve manter ao menos um item.",
)
def delete_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
) -> None:
    OrderService.delete_order_item(db, order_id, item_id)


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
