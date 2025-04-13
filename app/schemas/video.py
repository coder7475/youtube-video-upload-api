from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator

from app.schemas.base import BaseSchema


class VideoBase(BaseModel):
    """Base video schema with common fields."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="Video title")
    description: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    category_id: Optional[str] = None
    privacy_status: Optional[str] = Field("private", description="Video privacy: private, public, or unlisted")
    scheduled_time: Optional[datetime] = None
    
    @validator("privacy_status")
    def validate_privacy_status(cls, v):
        if v not in ["private", "public", "unlisted"]:
            raise ValueError("Privacy status must be 'private', 'public', or 'unlisted'")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            # Ensure tags is a comma-separated string
            tags = [tag.strip() for tag in v.split(",") if tag.strip()]
            return ",".join(tags)
        return v


class VideoCreate(VideoBase):
    """Schema for creating a new video schedule."""
    
    title: str = Field(..., min_length=1, max_length=100, description="Video title")
    scheduled_time: datetime = Field(..., description="Scheduled upload time (UTC)")
    # File path will be set by the server after file upload


class VideoUpdate(VideoBase):
    """Schema for updating an existing video schedule."""
    
    # All fields are optional for updates
    pass


class VideoInDB(VideoBase, BaseSchema):
    """Schema representing the database model for a video schedule."""
    
    user_id: str
    file_path: str
    thumbnail_path: Optional[str] = None
    status: str = "scheduled"
    youtube_video_id: Optional[str] = None
    result_message: Optional[str] = None


class VideoResponse(VideoInDB):
    """Schema for API responses with a video schedule."""
    
    # Include any computed properties here
    is_uploaded: bool = False
    youtube_url: Optional[str] = None
    
    @validator("is_uploaded", always=True)
    def set_is_uploaded(cls, v, values):
        return values.get("status") == "uploaded" and values.get("youtube_video_id") is not None
    
    @validator("youtube_url", always=True)
    def set_youtube_url(cls, v, values):
        video_id = values.get("youtube_video_id")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return None


class VideoFile(BaseModel):
    """Schema for video file upload."""
    
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scheduled_time: datetime
    tags: Optional[str] = None
    privacy_status: str = "private"

