from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/little_dragon")
logger.debug("Initializing database with URL: %s", DATABASE_URL)

# Create engine with echo=True for SQL query logging
engine = create_engine(
    DATABASE_URL,
    echo=True,  # This will log all SQL queries
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Set connection pool size
    max_overflow=10  # Allow up to 10 connections beyond pool_size
)
logger.debug("Database engine created with pool size: %d, max overflow: %d", 5, 10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.debug("Session maker configured")

Base = declarative_base()
logger.debug("Declarative base created")


# Dependency to get DB session
def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        logger.debug("Yielding database session")
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()
