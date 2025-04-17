import logging

from agents import trace
from fastapi import APIRouter, HTTPException, Depends

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


@router.post("/chat", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        current_user: User = Depends(get_current_user)
):
    """Handle chat requests with user authentication

    Args:
        request (ChatRequest): The chat request containing the message
        current_user (User): The authenticated user

    Returns:
        ChatResponse: The response containing the assistant's message
    """
    try:
        # Get or create session for the user
        user_id = current_user.id

        # Get existing messages from session
        with trace("Little Dragon Assistant Conversation", group_id=str(user_id)):
            response_content = await agent_service.get_agent_response(
                user_id=user_id,
                request=request
            )

            # Create response
            return ChatResponse(
                message=response_content,
                user_id=user_id
            )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )


@router.get("/messages")
async def get_messages(current_user: User = Depends(get_current_user)):
    """Get chat history for the authenticated user."""
    try:
        messages = agent_service.get_session_messages(current_user.id)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while getting messages: {str(e)}"
        )
