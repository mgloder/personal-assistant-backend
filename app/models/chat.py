from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: ChatMessage
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class AssistantContext(BaseModel):
    session_id: str
    assistant_name: str
