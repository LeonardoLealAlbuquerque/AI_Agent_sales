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