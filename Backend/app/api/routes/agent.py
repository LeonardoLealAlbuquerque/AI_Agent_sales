# app/api/routes/agent.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.agent import ChatRequest, ChatResponse
from app.agent.service import AgentService
from app.agent.llm_client import (
    BaseLLMClient,
    RealLLMClient,
    LLMTimeoutError,
    LLMUnavailableError,
    LLMError
)

router = APIRouter(prefix="/agent", tags=["Agent"])


def get_llm_client() -> BaseLLMClient:
    """Injeção de dependência para o cliente LLM, permitindo overrides fáceis nos testes."""
    return RealLLMClient()


def get_agent_service(llm_client: BaseLLMClient = Depends(get_llm_client)) -> AgentService:
    """Injeção de dependência do serviço orquestrador do Agente."""
    return AgentService(llm_client=llm_client)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def agent_chat(
    payload: ChatRequest,
    service: AgentService = Depends(get_agent_service)
) -> ChatResponse:
    """
    Endpoint principal para interação com o Agente B2B.
    
    Realiza o processamento da mensagem, controle de histórico e acionamento de
    ferramentas de análise de risco e crédito em modo Read-Only.
    """
    try:
        return service.run(payload)

    except LLMTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O serviço de IA excedeu o tempo limite de resposta. Tente novamente em instantes."
        ) from e

    except LLMUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O serviço de IA está temporariamente indisponível. Tente novamente mais tarde."
        ) from e

    except LLMError as e:
        print(f"Erro de comunicação com o modelo de IA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu uma falha interna na comunicação com o modelo de IA."
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno não tratado no processamento do agente."
        ) from e