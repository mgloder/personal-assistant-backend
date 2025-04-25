import uuid
from typing import List, Dict, AsyncGenerator

from agents import Agent, Runner, RunResult
from openai.types.responses import ResponseTextDeltaEvent

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

    async def get_agent_response(self, user_id: int, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Get agent response for a specific user as a streaming response."""
        input_messages = await self.get_context(user_id, request)
        stream_result = Runner.run_streamed(self.agent, input=input_messages)
        
        # Store the final result for context in future interactions
        self.chat_sessions[user_id] = stream_result
        
        # Stream the response chunks
        async for event in stream_result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield event.data.delta

    async def get_context(self, user_id: int, request: ChatRequest, records_limit=10):
        """Get context for a specific user, filtering top records."""
        history_run_result = self.chat_sessions.get(user_id, None)
        new_message = [{"role": request.message.role, "content": request.message.content}]
        if history_run_result is not None:
            input_messages = history_run_result.to_input_list() + new_message
        else:
            input_messages = new_message

        return input_messages[-records_limit:]
