import asyncio
import logging
from typing import Optional

from agents import trace
from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse

from ..config.settings import SESSION_COOKIE_MAX_AGE
from ..models.chat import ChatRequest, ChatResponse
from ..services.agent_service import AgentService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
agent_service = AgentService()


async def get_session(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = agent_service.get_or_create_session()
    return session_id


@router.get("/")
async def root():
    return {"message": "Welcome to Little Dragon Assistant API"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session_id: str = Depends(get_session)):
    """_summary_

    Args:
        request (ChatRequest): _description_
        session_id (str, optional): _description_. Defaults to Depends(get_session). session_id is also a conversation_id for tracing

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    try:
        # Get existing messages from session
        with trace("Little Dragon Assistant Conversation", group_id=session_id):
            response_content = await agent_service.get_agent_response(conversation_id=session_id,
                                                                    request=request)

            # Create response with session cookie
            response_data = ChatResponse(
                response=response_content,
                session_id=session_id
            )

        # Set session cookie
        response = JSONResponse(content=response_data.dict())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=SESSION_COOKIE_MAX_AGE,
            samesite="lax"
        )

        return response
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
