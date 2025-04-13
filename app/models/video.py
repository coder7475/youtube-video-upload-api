from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VideoStatus(str, Enum):
    """Enum for video upload status."""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    PROCESSING = "processing"
    UPLOADED = "uploaded"
    FAILED = "failed"


class VideoSchedule(BaseModel):
    """
    Model for scheduled video uploads.
    """
    
    # Ownership
    user_id = Column(String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="videos")
    
    # Video metadata
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    category_id = Column(String(50), nullable=True)  # YouTube category ID
    
    # File information
    file_path = Column(String(1024), nullable=False)
    thumbnail_path = Column(String(1024), nullable=True)
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default=VideoStatus.SCHEDULED, nullable=False)
    
    # Result information
    youtube_video_id = Column(String(50), nullable=True)  # ID of uploaded video
    result_message = Column(Text, nullable=True)  # For error messages or upload details
    
    # Privacy settings
    privacy_status = Column(String(20), default="private", nullable=False)  # private, public, unlisted
    
    def __repr__(self):
        return f"<VideoSchedule(id='{self.id}', title='{self.title}', status='{self.status}')>"
    
    @property
    def is_due(self) -> bool:
        """Check if the video is due for upload."""
        return datetime.utcnow() >= self.scheduled_time and self.status == VideoStatus.SCHEDULED

