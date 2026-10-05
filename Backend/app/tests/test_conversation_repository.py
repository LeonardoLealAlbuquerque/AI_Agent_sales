from app.repositories.conversation_repository import ConversationRepository


def test_add_message_persists_tool_calls_and_tool_name(db_session):
    repository = ConversationRepository(db_session)
    conversation = repository.create("Consulta de limite")
    db_session.commit()

    tool_calls = [{
        "id": "call-1",
        "type": "function",
        "function": {"name": "get_client_credit_limit", "arguments": "{}"},
    }]
    repository.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=None,
        tool_calls=tool_calls,
    )
    repository.add_message(
        conversation_id=conversation.id,
        role="tool",
        content='{"client_id": 1}',
        tool_call_id="call-1",
        name="get_client_credit_limit",
    )
    db_session.commit()

    history = repository.get_messages_for_llm(conversation.id)

    assert history == [
        {"role": "assistant", "content": None, "tool_calls": tool_calls},
        {
            "role": "tool",
            "content": '{"client_id": 1}',
            "tool_call_id": "call-1",
            "name": "get_client_credit_limit",
        },
    ]

def test_delete_conversation_endpoint_removes_conversation_and_messages(client, db_session):
    repository = ConversationRepository(db_session)
    conversation = repository.create("Conversa para excluir")
    repository.add_message(conversation.id, role="user", content="Mensagem de teste")
    db_session.commit()

    response = client.delete(f"/api/v1/agent/conversations/{conversation.id}")

    assert response.status_code == 204
    assert repository.get(conversation.id) is None
    assert repository.messages(conversation.id) == []
    assert client.get(f"/api/v1/agent/conversations/{conversation.id}").status_code == 404


def test_delete_missing_conversation_returns_404(client):
    response = client.delete("/api/v1/agent/conversations/missing-conversation")

    assert response.status_code == 404