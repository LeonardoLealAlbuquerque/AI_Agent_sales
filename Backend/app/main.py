from fastapi import FastAPI
from app.api.router import api_router
from app.api.errors import setup_exception_handlers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agente de Vendas B2B API",
    version="1.0.0",
    description="API de consultas comerciais e MVP de backend para o Agente B2B."
)

origins = [
    "http://localhost:5173",  # Porta padrão do Vite
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Caso use Next.js / React App
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API operando normalmente"}

app.include_router(api_router, prefix="/api/v1")