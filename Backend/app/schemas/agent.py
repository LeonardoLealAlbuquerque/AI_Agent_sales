# app/schemas/agent.py

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """Representa uma mensagem individual no histórico da conversa."""
    role: Literal["user", "assistant", "system", "tool"] = Field(
        ..., 
        description="Papel do emissor da mensagem no fluxo da conversa."
    )
    content: str = Field(
        ..., 
        description="Conteúdo textual da mensagem."
    )


class ToolCallInfo(BaseModel):
    """Detalhes das ferramentas acionadas pelo LLM durante o raciocínio."""
    tool_name: str = Field(..., description="Nome da ferramenta executada.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parâmetros de entrada passados para a ferramenta."
    )
    success: bool = Field(
        default=True, 
        description="Indica se a execução da ferramenta ocorreu sem exceções."
    )


class ChatRequest(BaseModel):
    """Schema de entrada (payload) para o endpoint de chat do agente."""
    message: str = Field(
        ..., 
        min_length=1, 
        description="Mensagem do usuário enviada para o agente B2B."
    )
    conversation_id: Optional[str] = Field(
        default=None, 
        description="Identificador opcional da conversa para rastreabilidade de sessão."
    )
    history: List[ChatMessage] = Field(
        default_factory=list, 
        description="Histórico opcional de mensagens anteriores da sessão."
    )

    @field_validator("message")
    @classmethod
    def validate_non_empty_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("A mensagem enviada não pode estar em branco.")
        return v.strip()


class ChatResponse(BaseModel):
    """Schema de saída (resposta) retornado pelo agente ao cliente."""
    conversation_id: Optional[str] = Field(
        default=None, 
        description="Identificador da conversa mantido na resposta."
    )
    response: str = Field(
        ..., 
        description="Resposta textual final gerada pelo agente de IA."
    )
    tools_used: List[ToolCallInfo] = Field(
        default_factory=list, 
        description="Lista e status de todas as ferramentas acionadas durante a requisição."
    )
    error: Optional[str] = Field(
        default=None, 
        description="Mensagem de erro amigável e publicável (sem detalhes sensíveis de infraestrutura/banco)."
    )