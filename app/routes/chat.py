import asyncio
import logging
from typing import Optional

from agents import trace
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.chat import ChatRequest, ChatResponse
from ..services.agent_service import AgentService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
agent_service = AgentService()


async def get_session(session_id: Optional[str] = None):
    if not session_id:
        session_id = agent_service.get_or_create_session()
    return session_id


@router.get("/")
async def root():
    session_id = agent_service.get_or_create_session()
    return {"message": "Welcome to Little Dragon Assistant API", "session_id": session_id}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests with session management

    Args:
        request (ChatRequest): The chat request containing the message and optional session_id

    Returns:
        ChatResponse: The response containing the assistant's message and session ID
    """
    try:
        # Get or create session ID from request
        session_id = await get_session(request.session_id)

        # Get existing messages from session
        with trace("Little Dragon Assistant Conversation", group_id=session_id):
            response_content = await agent_service.get_agent_response(conversation_id=session_id,
                                                                    request=request)

            # Create response with session ID
            response_data = ChatResponse(
                response=response_content,
                session_id=session_id
            )

        return response_data
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    try:
        messages = agent_service.get_session_messages(session_id)
        if not messages:
            logger.error(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error in get_session_messages endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
