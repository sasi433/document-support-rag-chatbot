from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question cannot be empty")
        return question


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
