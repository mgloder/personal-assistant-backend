from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: Message


class ChatResponse(BaseModel):
    message: str
    user_id: int


class AssistantContext(BaseModel):
    user_id: int
    assistant_name: str
