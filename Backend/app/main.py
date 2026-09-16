from fastapi import FastAPI
from app.api.router import api_router
from app.api.errors import setup_exception_handlers

app = FastAPI(
    title="Agente de Vendas B2B API",
    version="1.0.0",
    description="API de consultas comerciais e MVP de backend para o Agente B2B."
)

setup_exception_handlers(app)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API operando normalmente"}

app.include_router(api_router, prefix="/api/v1")