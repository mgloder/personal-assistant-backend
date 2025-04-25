from typing import List, Dict, AsyncGenerator

from agents import Agent, Runner, RunResult
from openai.types.responses import ResponseTextDeltaEvent
from mem0 import MemoryClient

from ..config.settings import (
    OPENAI_MODEL,
    MEM0_API_KEY
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
        self.mem0_client = MemoryClient(api_key=MEM0_API_KEY)

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
        
        # Collect the full response
        full_response = ""
        
        # Stream the response chunks
        async for event in stream_result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_response += event.data.delta
                yield event.data.delta
        
        # Save the complete agent response to mem0
        self.mem0_client.add(
            messages=[{
                "role": "assistant",
                "content": full_response
            }],
            user_id=str(user_id),
            metadata={"message_type": "assistant"}
        )

    async def get_context(self, user_id: int, request: ChatRequest, records_limit=10):
        """Get context for a specific user from mem0 using semantic search."""
        # Save the new user message to mem0
        self.mem0_client.add(
            messages=[{
                "role": request.message.role,
                "content": request.message.content
            }],
            user_id=str(user_id),
            metadata={"message_type": "user"}
        )
        
        # Search for relevant context using the user's message
        search_results = self.mem0_client.search(
            query=request.message.content,
            user_id=str(user_id),
            limit=records_limit
        )
        
        # Convert search results to the expected format
        input_messages = [
            {
                "role": result["metadata"]["message_type"] if result.get("metadata") else "user",
                "content": result["memory"]
            }
            for result in search_results
        ]
        
        # Add the current message at the end
        input_messages.append({
            "role": request.message.role,
            "content": request.message.content
        })
        
        return input_messages
