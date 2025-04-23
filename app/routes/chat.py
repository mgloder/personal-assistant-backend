import logging
from typing import AsyncGenerator

from agents import trace
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models.chat import ChatRequest, ChatResponse
from ..models.user import User
from ..services.agent_service import AgentService
from ..utils.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
agent_service = AgentService()


async def get_session(user: User):
    """Get or create a session for the authenticated user."""
    return agent_service.get_or_create_session(user.id)


@router.get("/")
async def root():
    """Public endpoint for API health check"""
    return {"message": "Welcome to Little Dragon Assistant API"}


@router.post("/chat")
async def chat(
        request: ChatRequest,
        current_user: User = Depends(get_current_user)
):
    """Handle chat requests with user authentication and stream the response

    Args:
        request (ChatRequest): The chat request containing the message
        current_user (User): The authenticated user

    Returns:
        StreamingResponse: A streaming response containing the assistant's message chunks
    """
    try:
        # Get or create session for the user
        user_id = current_user.id

        # Create a generator function to stream the response
        async def stream_response() -> AsyncGenerator[str, None]:
            with trace("Little Dragon Assistant Conversation", group_id=str(user_id)):
                async for chunk in agent_service.get_agent_response(
                    user_id=user_id,
                    request=request
                ):
                    yield f"data: {chunk}\n\n"

        # Return a streaming response
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
