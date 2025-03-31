from openai import OpenAI
from typing import List, Dict
import uuid
from ..config.settings import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS
)

class ChatService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.chat_sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_or_create_session(self, session_id: str = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
            self.chat_sessions[session_id] = []
        return session_id

    def get_session_messages(self, session_id: str) -> List[Dict[str, str]]:
        return self.chat_sessions.get(session_id, [])

    def add_messages_to_session(self, session_id: str, messages: List[Dict[str, str]]) -> None:
        session_messages = self.chat_sessions.get(session_id, [])
        session_messages.extend(messages)
        self.chat_sessions[session_id] = session_messages

    async def get_chat_response(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        return response.choices[0].message.content 