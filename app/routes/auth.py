from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, User as UserSchema
from ..utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    blacklist_token
)

router = APIRouter()


# Add a new model for email lookup
class EmailLookup(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/user-by-email", response_model=UserSchema)
def get_user_by_email(email_lookup: EmailLookup, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email_lookup.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login")
async def login_json(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(data={"sub": user.email})
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }


@router.post("/logout")
async def logout(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Logout the current user and blacklist their token.
    This endpoint is protected and requires authentication.
    """
    # Get the token from the request header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # Add the token to the blacklist
        blacklist_token(token, db)

    return {
        "success": True,
        "message": "Successfully logged out"
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
