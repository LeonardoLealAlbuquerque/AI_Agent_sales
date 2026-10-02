import pytest
from sqlalchemy import func, select
from unittest.mock import MagicMock, patch

from app.agent.service import AgentService
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.invoice import Invoice
from app.schemas.agent import ChatRequest
from app.repositories.conversation_repository import ConversationRepository
from app.services.chromadb_service import ChromaDBService


@pytest.fixture
def prepare_chroma_kb(tmp_path):
    """Inicializa uma base do ChromaDB temporária e ingere dados simulados do Playbook."""
    test_dir = str(tmp_path / "chroma_integration_db")
    service = ChromaDBService(
        persist_directory=test_dir, 
        collection_name="test_integration_kb"
    )
    
    md_content = """# Playbook de Negociação B2B
## Descontos e Alçadas
O vendedor opera em alçada zero. Descontos acima de 5% exigem aprovação do gerente comercial.
Prazos superiores a 30 dias devem ser submetidos à análise de risco de crédito.
"""
    file_path = tmp_path / "playbook_test.md"
    file_path.write_text(md_content, encoding="utf-8")
    service.ingest_playbook(file_path=str(file_path), force_recreate=True)
    return service


def llm_response(content=None, tool_calls=None):
    response = MagicMock()
    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = tool_calls
    return response


def test_agent_rag_tool_invocation_and_snippet_return(prepare_chroma_kb):
    """Testa busca RAG, retorno de trecho e continuidade do historico."""
    mock_llm = MagicMock()

    mock_tool_call = {
        "id": "call_rag_001",
        "type": "function",
        "function": {
            "name": "buscar_regras_negociacao",
            "arguments": '{"query": "desconto para pagamento à vista"}'
        }
    }
    mock_llm.chat_completion.side_effect = [
        llm_response(tool_calls=[mock_tool_call]),
        llm_response(
            content="Conforme o Playbook, você opera sob alçada zero. Descontos exigem aprovação gerencial."
        ),
    ]

    with patch("app.agent.tools.chroma_service", prepare_chroma_kb):
        response = AgentService(llm_client=mock_llm).run(
            ChatRequest(message="Qual a regra de desconto?")
        )

    assert "alçada zero" in response.response
    assert mock_llm.chat_completion.call_count == 2
    message_history = mock_llm.chat_completion.call_args_list[-1].kwargs["messages"]
    assert [msg["role"] for msg in message_history] == ["system", "user", "assistant", "tool"]
    tool_msg = next(msg for msg in message_history if msg["role"] == "tool")
    assert tool_msg["tool_call_id"] == "call_rag_001"
    assert "alçada zero" in tool_msg["content"].lower()


def test_agent_handling_kb_unavailable():
    """
    Testa a resiliência do agente tratando exceções de indisponibilidade da KB (RAG-FR-005).
    """
    mock_llm = MagicMock()

    mock_tool_call = {
        "id": "call_rag_err",
        "type": "function",
        "function": {
            "name": "buscar_regras_negociacao",
            "arguments": '{"query": "política de parcelamento"}'
        }
    }
    mock_llm.chat_completion.side_effect = [
        llm_response(tool_calls=[mock_tool_call]),
        llm_response(content="Desculpe, a base de conhecimento está temporariamente indisponível."),
    ]

    mock_failing_chroma = MagicMock()
    mock_failing_chroma.search_similarity.side_effect = RuntimeError("Falha de conexão com o ChromaDB")

    with patch("app.agent.tools.chroma_service", mock_failing_chroma):
        AgentService(llm_client=mock_llm).run(
            ChatRequest(message="Quais as regras de parcelamento?")
        )

        message_history = mock_llm.chat_completion.call_args_list[-1].kwargs["messages"]
        tool_msg = next(msg for msg in message_history if msg["role"] == "tool")
        assert "indisponível" in tool_msg["content"].lower() or "error" in tool_msg["content"].lower()


def test_agent_inclui_historico_e_instrucao_de_continuidade_em_followup(db):
    repository = ConversationRepository(db)
    conversation = repository.create("Limite e risco do cliente")
    repository.add_message(
        conversation.id,
        role="user",
        content="Consulte o limite da Risco Elevado LTDA.",
    )
    repository.add_message(
        conversation.id,
        role="assistant",
        content=None,
        tool_calls=[{
            "id": "call-credit",
            "type": "function",
            "function": {
                "name": "get_client_credit_limit",
                "arguments": '{"client_id": 2}',
            },
        }],
    )
    repository.add_message(
        conversation.id,
        role="tool",
        content='{"client_id": 2, "credit_limit": 10000}',
        tool_call_id="call-credit",
        name="get_client_credit_limit",
    )
    repository.add_message(
        conversation.id,
        role="assistant",
        content="O limite disponível é R$ 8.500,00.",
    )
    db.commit()

    mock_llm = MagicMock()
    mock_llm.chat_completion.return_value = llm_response(content="Vou consultar o risco.")
    AgentService(llm_client=mock_llm, db=db).run(ChatRequest(
        message="Com base na resposta anterior, qual é o risco dela?",
        conversation_id=conversation.id,
    ))

    llm_messages = mock_llm.chat_completion.call_args.kwargs["messages"]
    assert "Continuidade Conversacional" in llm_messages[0]["content"]
    assert any(
        message.get("tool_call_id") == "call-credit"
        and '"client_id": 2' in message["content"]
        for message in llm_messages
        if message["role"] == "tool"
    )
    assert llm_messages[-1]["content"] == "Com base na resposta anterior, qual é o risco dela?"


def test_conversation_history_hides_internal_tool_messages(client, db):
    repository = ConversationRepository(db)
    conversation = repository.create("Consulta com ferramenta")
    repository.add_message(
        conversation.id,
        role="user",
        content="Qual o limite do cliente?",
    )
    repository.add_message(
        conversation.id,
        role="assistant",
        content=None,
        tool_calls=[{
            "id": "call-credit",
            "type": "function",
            "function": {"name": "get_client_credit_limit", "arguments": "{}"},
        }],
    )
    repository.add_message(
        conversation.id,
        role="tool",
        content='{"total_clients": 1, "clients": [{"company_name": "Risco Elevado LTDA"}]}',
        tool_call_id="call-credit",
        name="list_clients",
    )
    repository.add_message(
        conversation.id,
        role="assistant",
        content="O limite disponível é R$ 8.500,00.",
    )
    db.commit()

    response = client.get(f"/api/v1/agent/conversations/{conversation.id}")

    assert response.status_code == 200
    assert response.json()["messages"] == [
        {"role": "user", "content": "Qual o limite do cliente?"},
        {"role": "assistant", "content": "O limite disponível é R$ 8.500,00."},
    ]


def test_agent_rag_query_does_not_mutate_database():
    """
    Garante que consultas de política/RAG não realizam nenhuma mutação no banco relacional SQLite (Read-Only).
    """
    def count_records():
        db = SessionLocal()
        try:
            return (
                db.scalar(select(func.count()).select_from(Client)),
                db.scalar(select(func.count()).select_from(Invoice)),
            )
        finally:
            db.close()

    initial_clients, initial_invoices = count_records()

    mock_llm = MagicMock()
    mock_llm.chat_completion.return_value = llm_response(
        content="A consulta de regras foi processada com sucesso sem alterações."
    )

    agent = AgentService(llm_client=mock_llm)
    agent.run(ChatRequest(message="Consulte as regras de prazo de pagamento."))

    final_clients, final_invoices = count_records()

    assert initial_clients == final_clients
    assert initial_invoices == final_invoices