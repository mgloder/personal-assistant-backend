import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Settings
API_TITLE = "Little Dragon Assistant API"
API_VERSION = "1.0.0"

# Security Settings
SESSION_SECRET = os.getenv("SESSION_SECRET", os.getenv("SESSION_SECRET_KEY", "your-secret-key-here"))
SESSION_COOKIE_MAX_AGE = 3600  # 1 hour

# CORS Settings
CORS_ORIGINS = ["http://localhost:3001", "http://192.168.31.224:3001", "http://0.0.0.0:3001"]

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 1000
