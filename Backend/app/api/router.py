from fastapi import APIRouter
from app.api.routes import client, credit, order, invoicing, risk, agent

api_router = APIRouter()

api_router.include_router(client.router)
api_router.include_router(credit.router)
api_router.include_router(order.router)
api_router.include_router(order.router_clientes)
api_router.include_router(invoicing.router)
api_router.include_router(invoicing.router_all)
api_router.include_router(risk.router)
api_router.include_router(agent.router)