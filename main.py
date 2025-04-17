from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from app.routes import chat, auth
from app.config.settings import API_TITLE, CORS_ORIGINS

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Starting application with log level: %s", log_level)

app = FastAPI(title=API_TITLE)

# Configure CORS with more detailed settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug("Incoming request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", dict(request.headers))

    response = await call_next(request)

    logger.debug("Response status: %d", response.status_code)
    logger.debug("Response headers: %s", dict(response.headers))
    return response


# Include routers
logger.debug("Including routers: chat, auth")
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])


@app.on_event("startup")
async def startup_event():
    logger.debug("Application startup")
    logger.debug("CORS origins: %s", CORS_ORIGINS)


@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("Application shutdown")


if __name__ == "__main__":
    import uvicorn

    logger.debug("Starting uvicorn server on 0.0.0.0:8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)
