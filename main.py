from fastapi import FastAPI, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from openai import OpenAI
import uuid
from itsdangerous import URLSafeTimedSerializer
import logging

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Little Dragon Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize serializer for session data
SECRET_KEY = os.getenv("SESSION_SECRET", os.getenv("SESSION_SECRET_KEY", "your-secret-key-here"))
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    session_id: str

# In-memory storage for chat sessions (in production, use a database)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

async def get_session(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = []
    return session_id

@app.get("/")
async def root():
    return {"message": "Welcome to Little Dragon Assistant API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session_id: str = Depends(get_session)):
    try:
        # Get existing messages from session
        session_messages = chat_sessions.get(session_id, [])
        
        # Add new messages to session
        new_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        session_messages.extend(new_messages)
        chat_sessions[session_id] = session_messages
        
        # Call OpenAI API with all session messages
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Add assistant's response to session
        assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
        chat_sessions[session_id].append(assistant_message)
        
        # Create response with session cookie
        response_data = ChatResponse(
            response=response.choices[0].message.content,
            session_id=session_id
        )
        
        # Set session cookie
        response = JSONResponse(content=response_data.dict())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=3600,  # 1 hour
            samesite="lax"
        )
        
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    try:
        if session_id not in chat_sessions:
            logger.error(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        return {"messages": chat_sessions[session_id]}
    except Exception as e:
        logger.error(f"Error in get_session_messages endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 