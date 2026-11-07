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

    def messages_before(
        self,
        conversation_id: str,
        before_id: int | None = None,
        limit: int = 50,
        after_id: int | None = None,
    ) -> List[ChatMessageRecord]:
        statement = select(ChatMessageRecord).where(
            ChatMessageRecord.conversation_id == conversation_id
        )
        if before_id is not None:
            statement = statement.where(ChatMessageRecord.id < before_id)
        if after_id is not None:
            statement = statement.where(ChatMessageRecord.id > after_id)
        statement = statement.order_by(ChatMessageRecord.id.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def messages_for_summary(
        self,
        conversation_id: str,
        after_id: int | None,
        before_id: int,
        limit: int = 50,
    ) -> List[ChatMessageRecord]:
        statement = (
            select(ChatMessageRecord)
            .where(
                ChatMessageRecord.conversation_id == conversation_id,
                ChatMessageRecord.id < before_id,
            )
            .order_by(ChatMessageRecord.id)
            .limit(limit)
        )
        if after_id is not None:
            statement = statement.where(ChatMessageRecord.id > after_id)
        return list(self.db.scalars(statement).all())

    @staticmethod
    def format_message(record: ChatMessageRecord) -> dict[str, Any]:
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

        return msg

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
        return [self.format_message(record) for record in records]

    def update_summary(
        self,
        conversation_id: str,
        summary: str,
        through_message_id: int | None,
    ) -> None:
        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError("Conversa não encontrada.")
        conversation.summary = summary
        if through_message_id is not None:
            conversation.summary_through_message_id = through_message_id