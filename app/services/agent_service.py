import uuid
from typing import List, Dict

from agents import Agent, Runner, RunResult

from ..config.settings import (
    OPENAI_MODEL
)
from ..models.chat import AssistantContext, ChatRequest


class AgentService:
    def __init__(self):
        self.chat_sessions: Dict[str, RunResult] = {}
        self.agent = Agent[AssistantContext](
            name="little_dragon",
            instructions="You are a helpful personal assistant",
            model=OPENAI_MODEL
        )

    def get_or_create_session(self, session_id: str = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
        return session_id

    def get_session_messages(self, session_id: str) -> List[Dict[str, str]]:
        return self.chat_sessions.get(session_id, [])

    async def get_agent_response(self, conversation_id: str, request: ChatRequest):
        input_messages = await self.get_context(conversation_id, request)
        new_result = await Runner.run(self.agent, input_messages)
        self.chat_sessions[conversation_id] = new_result
        return new_result.final_output

    async def get_context(self, conversation_id, request, records_limit=10):
        """filter top 10 records as context"""
        history_run_result = self.chat_sessions.get(conversation_id, None)
        new_message = [{"role": request.message.role, "content": request.message.content}]
        if history_run_result is not None:
            input_messages = history_run_result.to_input_list() + new_message
        else:
            input_messages = new_message

        return input_messages[:records_limit]
