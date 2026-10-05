from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.chat_message import ChatMessageRecord
from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db
        Base.metadata.create_all(bind=db.get_bind())

    def get(self, conversation_id: str) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    def delete(self, conversation: Conversation) -> None:
        self.db.delete(conversation)

    def create(self, title: str) -> Conversation:
        conversation = Conversation(title=title)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def list(self, limit: int = 50) -> Sequence[Conversation]:
        statement = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def messages(self, conversation_id: str) -> Sequence[ChatMessageRecord]:
        statement = (
            select(ChatMessageRecord)
            .where(ChatMessageRecord.conversation_id == conversation_id)
            .order_by(ChatMessageRecord.created_at, ChatMessageRecord.id)
        )
        return self.db.scalars(statement).all()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str | None,
        tool_call_id: str | None = None,
        name: str | None = None,
        tool_calls: List[Dict[str, Any]] | None = None,
    ) -> ChatMessageRecord:
        message = ChatMessageRecord(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            tool_calls=tool_calls,
        )
        self.db.add(message)
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is not None:
            conversation.updated_at = datetime.now(timezone.utc)
        return message

    def get_messages_for_llm(self, conversation_id: str) -> List[dict[str, Any]]:
        records = self.messages(conversation_id)
        formatted: list[dict[str, Any]] = []

        for record in records:
            msg: dict[str, Any] = {"role": record.role}

            if record.content is not None:
                msg["content"] = record.content
            elif record.role == "assistant":
                msg["content"] = None

            if record.tool_calls:
                msg["tool_calls"] = record.tool_calls

            if record.tool_call_id:
                msg["tool_call_id"] = record.tool_call_id

            if record.name:
                msg["name"] = record.name

            formatted.append(msg)

        return formatted