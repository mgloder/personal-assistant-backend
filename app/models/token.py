from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from ..config.database import Base

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_on = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=True, nullable=False) 