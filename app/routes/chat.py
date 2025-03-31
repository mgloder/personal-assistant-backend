from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from ..models.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService
from ..config.settings import SESSION_COOKIE_MAX_AGE

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
chat_service = ChatService()

async def get_session(session_id: Optional[str] = Cookie(None)):
    return chat_service.get_or_create_session(session_id)

@router.get("/")
async def root():
    return {"message": "Welcome to Little Dragon Assistant API"}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session_id: str = Depends(get_session)):
    try:
        # Get existing messages from session
        session_messages = chat_service.get_session_messages(session_id)
        
        # Add new messages to session
        new_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        chat_service.add_messages_to_session(session_id, new_messages)
        
        # Get response from OpenAI
        response_content = await chat_service.get_chat_response(session_messages + new_messages)
        
        # Add assistant's response to session
        assistant_message = {"role": "assistant", "content": response_content}
        chat_service.add_messages_to_session(session_id, [assistant_message])
        
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
        messages = chat_service.get_session_messages(session_id)
        if not messages:
            logger.error(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error in get_session_messages endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 