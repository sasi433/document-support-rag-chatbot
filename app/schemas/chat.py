from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.file_utils import validate_document_filename

MAX_CHAT_MESSAGE_LENGTH = 2000
MAX_CONVERSATION_MESSAGES = 6
MAX_SELECTED_DOCUMENTS = 20


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_CHAT_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("Message content cannot be empty")
        return content


class ChatRequest(BaseModel):
    question: str = Field(max_length=MAX_CHAT_MESSAGE_LENGTH)
    history: list[ConversationMessage] = Field(
        default_factory=list,
        max_length=MAX_CONVERSATION_MESSAGES,
    )
    documents: list[str] = Field(
        default_factory=list,
        max_length=MAX_SELECTED_DOCUMENTS,
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question cannot be empty")
        return question

    @field_validator("history")
    @classmethod
    def validate_history(
        cls,
        value: list[ConversationMessage],
    ) -> list[ConversationMessage]:
        if len(value) % 2 != 0:
            raise ValueError("History must contain complete user/assistant pairs")

        for index, message in enumerate(value):
            expected_role = "user" if index % 2 == 0 else "assistant"
            if message.role != expected_role:
                raise ValueError("History roles must alternate user and assistant")

        return value

    @field_validator("documents")
    @classmethod
    def validate_documents(cls, value: list[str]) -> list[str]:
        documents = [validate_document_filename(filename) for filename in value]
        if len(set(documents)) != len(documents):
            raise ValueError("Selected documents must be unique")
        return documents


class SourceReference(BaseModel):
    filename: str
    chunk_index: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
