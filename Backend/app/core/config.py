import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # Configurações gerais da API (Spec 001)
    PROJECT_NAME: str = "B2B Sales Agent API"
    
    # Configurações do LLM (Spec 002 - T046)
    LLM_PROVIDER: str = Field(default="openai", validation_alias="LLM_PROVIDER")
    LLM_MODEL: str = Field(default="gpt-4o", validation_alias="LLM_MODEL")
    LLM_API_KEY: str = Field(default="", validation_alias="LLM_API_KEY")
    LLM_BASE_URL: str = Field(default="", validation_alias="LLM_BASE_URL")
    LLM_TIMEOUT: int = Field(default=30, validation_alias="LLM_TIMEOUT")
    LLM_MAX_TOKENS: int = Field(default=2000, validation_alias="LLM_MAX_TOKENS")

    @field_validator("LLM_API_KEY", mode="before")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        # Verifica se o valor está vazio ou se manteve o texto de exemplo padrão
        if not v or not v.strip() or v == "sua_chave_da_openai_aqui":
            env_key = os.getenv("LLM_API_KEY", "")
            if not env_key or env_key == "sua_chave_da_openai_aqui" or not env_key.strip():
                raise ValueError(
                    "\n❌ [Erro de Configuração - T046]: A chave de API do LLM (LLM_API_KEY) é obrigatória. "
                    "Copie o arquivo .env.example para .env e preencha sua chave de API válida da OpenAI."
                )
            return env_key
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"

# Instância global de configurações
settings = Settings()