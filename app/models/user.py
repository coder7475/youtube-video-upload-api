from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # YouTube OAuth fields
    youtube_token = Column(String(2048), nullable=True)
    youtube_refresh_token = Column(String(255), nullable=True)
    youtube_token_expiry = Column(String(50), nullable=True)
    
    # Relationships
    videos = relationship("VideoSchedule", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"

