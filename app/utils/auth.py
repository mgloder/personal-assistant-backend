from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..config.settings import SESSION_SECRET
from ..models.user import User
from ..models.token import BlacklistedToken

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use HTTPBearer instead of OAuth2PasswordBearer to prevent auto-redirect
security = HTTPBearer(auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SESSION_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def is_token_blacklisted(token: str, db: Session) -> bool:
    """Check if a token is blacklisted."""
    blacklisted_token = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token,
        BlacklistedToken.is_revoked == True
    ).first()
    return blacklisted_token is not None

def blacklist_token(token: str, db: Session) -> None:
    """Add a token to the blacklist."""
    try:
        # Decode the token to get its expiration
        payload = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp)
            
            # Create a new blacklisted token record
            blacklisted_token = BlacklistedToken(
                token=token,
                expires_at=expires_at
            )
            db.add(blacklisted_token)
            db.commit()
    except JWTError:
        # If token is invalid, we don't need to blacklist it
        pass

async def get_current_user(request: Request, token: Optional[HTTPBearer] = Depends(security), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ')[1]
        else:
            raise credentials_exception
    else:
        token_str = token.credentials

    # Check if token is blacklisted
    if is_token_blacklisted(token_str, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token_str, SESSION_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_optional_user(token: str = Depends(security), db: Session = Depends(get_db)) -> Optional[User]:
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None 