# app/api/routes/agent.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.agent import ChatRequest, ChatResponse, ChatMessage, ConversationHistory, ConversationSummary
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


def get_agent_service(
    llm_client: BaseLLMClient = Depends(get_llm_client),
    db: Session = Depends(get_db),
) -> AgentService:
    """Injeção de dependência do serviço orquestrador do Agente."""
    return AgentService(llm_client=llm_client, db=db)


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    return [
        ConversationSummary(
            conversation_id=item.id,
            title=item.title,
            created_at=item.created_at.isoformat() if item.created_at else None,
            updated_at=item.updated_at.isoformat() if item.updated_at else None,
        )
        for item in ConversationRepository(db).list(limit)
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationHistory:
    repository = ConversationRepository(db)
    conversation = repository.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")
    return ConversationHistory(
        conversation_id=conversation.id,
        title=conversation.title,
        messages=[
            ChatMessage(role=item.role, content=item.content)
            for item in repository.messages(conversation.id)
            if item.role in {"user", "assistant"}
            and not item.tool_calls
            and item.content
        ],
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir conversa do histórico",
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> None:
    repository = ConversationRepository(db)
    conversation = repository.get(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada.",
        )

    repository.delete(conversation)
    db.commit()


@router.post("/chat", status_code=status.HTTP_200_OK, response_class=StreamingResponse)
def agent_chat(
    payload: ChatRequest,
    service: AgentService = Depends(get_agent_service)
) -> StreamingResponse:
    """
    Endpoint principal para interação com o Agente B2B.
    
    Realiza o processamento da mensagem, controle de histórico e acionamento de
    ferramentas de análise de risco e crédito em modo Read-Only.
    """
    try:
        gerador = service.run(payload)
        return StreamingResponse(
            gerador, 
            media_type="text/plain"  
        )

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

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno não tratado no processamento do agente."
        ) from e