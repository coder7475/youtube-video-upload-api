from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate, Token

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user.
    """
    # Check if user with the same email exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if user with the same username exists
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Create new user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Try to find user by username first
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # If not found, try by email
    if not user:
        user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Create access token with 24 hour expiry
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information.
    """
    # Add computed property for YouTube auth status
    result = UserSchema.model_validate(current_user)
    result.has_youtube_auth = bool(current_user.youtube_token)
    return result


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user information.
    """
    # Update user fields
    for field in user_in.model_dump(exclude_unset=True).keys():
        if field == "password" and user_in.password:
            setattr(current_user, "hashed_password", get_password_hash(user_in.password))
        elif hasattr(current_user, field) and field != "password":
            setattr(current_user, field, getattr(user_in, field))
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    # Add computed property for YouTube auth status
    result = UserSchema.model_validate(current_user)
    result.has_youtube_auth = bool(current_user.youtube_token)
    return result


@router.delete("/me", response_model=BaseResponse)
def delete_user_me(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete current user.
    """
    db.delete(current_user)
    db.commit()
    
    return {
        "success": True,
        "message": "User deleted successfully",
    }

