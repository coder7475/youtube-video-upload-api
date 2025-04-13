from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    
    success: bool = True
    message: str = "Operation successful"
    data: Optional[dict] = None


class PaginationParams(BaseModel):
    """Parameters for pagination."""
    
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class PaginatedResponse(BaseModel):
    """Response for paginated results."""
    
    items: list
    total: int
    page: int
    size: int
    pages: int

