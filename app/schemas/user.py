from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema


class UserBase(BaseModel):
    """Base user schema."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for user creation."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserUpdate(UserBase):
    """Schema for user updates."""
    
    password: Optional[str] = Field(None, min_length=8)


class UserInDBBase(UserBase, BaseSchema):
    """Base schema for users in DB (with ID and timestamps)."""
    pass


class User(UserInDBBase):
    """Public user schema (returned to clients)."""
    
    # YouTube-specific fields
    has_youtube_auth: bool = False


class UserInDB(UserInDBBase):
    """Internal user schema with password hash."""
    
    hashed_password: str
    youtube_token: Optional[str] = None
    youtube_refresh_token: Optional[str] = None
    youtube_token_expiry: Optional[str] = None


class Token(BaseModel):
    """Schema for authentication tokens."""
    
    access_token: str
    token_type: str = "bearer"
    

class TokenPayload(BaseModel):
    """Schema for token payload."""
    
    sub: str  # Subject (user ID)
    exp: int  # Expiration time (Unix timestamp)

