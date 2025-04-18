import uuid
from typing import List, Dict

from agents import Agent, Runner, RunResult

from ..config.settings import (
    OPENAI_MODEL
)
from ..models.chat import AssistantContext, ChatRequest


class AgentService:
    def __init__(self):
        self.chat_sessions: Dict[int, RunResult] = {}
        self.agent = Agent[AssistantContext](
            name="little_dragon",
            instructions="You are a helpful personal assistant",
            model=OPENAI_MODEL
        )

    def get_or_create_session(self, user_id: int) -> int:
        """Get or create a session for a user. Now requires user_id."""
        if not user_id:
            raise ValueError("user_id is required")
        return user_id

    def get_session_messages(self, user_id: int) -> List[Dict[str, str]]:
        """Get messages for a specific user."""
        return self.chat_sessions.get(user_id, [])

    async def get_agent_response(self, user_id: int, request: ChatRequest):
        """Get agent response for a specific user."""
        input_messages = await self.get_context(user_id, request)
        new_result = await Runner.run(self.agent, input_messages)
        self.chat_sessions[user_id] = new_result
        return new_result.final_output

    async def get_context(self, user_id: int, request: ChatRequest, records_limit=10):
        """Get context for a specific user, filtering top records."""
        history_run_result = self.chat_sessions.get(user_id, None)
        new_message = [{"role": request.message.role, "content": request.message.content}]
        if history_run_result is not None:
            input_messages = history_run_result.to_input_list() + new_message
        else:
            input_messages = new_message

        return input_messages[:records_limit]
