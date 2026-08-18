from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    conversation_id: str | None = None
    stream: bool = False

class ChatResponse(BaseModel):
    answer: str
    nexus: dict
