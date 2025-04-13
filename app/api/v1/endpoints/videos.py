from datetime import datetime
import os
import shutil
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.video import VideoSchedule, VideoStatus
from app.schemas.base import BaseResponse, PaginationParams
from app.schemas.video import VideoCreate, VideoResponse, VideoUpdate, VideoFile

router = APIRouter()


@router.get("/", response_model=List[VideoResponse])
def list_videos(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> Any:
    """
    Retrieve all video schedules for the current user.
    """
    query = db.query(VideoSchedule).filter(VideoSchedule.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(VideoSchedule.status == status)
    
    # Apply pagination
    total = query.count()
    videos = query.order_by(VideoSchedule.scheduled_time.desc()).offset(skip).limit(limit).all()
    
    return videos


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str = Path(..., description="The ID of the video to retrieve"),
) -> Any:
    """
    Get a specific video schedule by ID.
    """
    video = db.query(VideoSchedule).filter(
        VideoSchedule.id == video_id,
        VideoSchedule.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    return video


@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=100),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    privacy_status: str = Form("private"),
    scheduled_time: datetime = Form(...),
) -> Any:
    """
    Create a new video schedule with file upload.
    """
    # Validate privacy status
    if privacy_status not in ["private", "public", "unlisted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privacy status must be 'private', 'public', or 'unlisted'",
        )
    
    # Ensure the scheduled time is in the future
    if scheduled_time <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future",
        )
    
    # Check if current_user has YouTube authentication
    if not current_user.youtube_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube account not connected. Please authorize with YouTube first.",
        )
    
    # Create user upload directory if it doesn't exist
    user_upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        settings.UPLOAD_DIR,
        current_user.id
    )
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Generate unique filename and save the file
    file_extension = os.path.splitext(video_file.filename)[1].lower()
    file_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{file_extension}"
    file_path = os.path.join(user_upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)
    
    # Create new video schedule
    new_video = VideoSchedule(
        user_id=current_user.id,
        title=title,
        description=description,
        tags=tags,
        category_id=category_id,
        file_path=file_path,
        scheduled_time=scheduled_time,
        status=VideoStatus.SCHEDULED,
        privacy_status=privacy_status,
    )
    
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    
    return new_video


@router.put("/{video_id}", response_model=VideoResponse)
def update_video_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str = Path(..., description="The ID of the video to update"),
    video_in: VideoUpdate,
) -> Any:
    """
    Update an existing video schedule.
    """
    video = db.query(VideoSchedule).filter(
        VideoSchedule.id == video_id,
        VideoSchedule.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Prevent updates to videos that are already being processed or uploaded
    if video.status not in [VideoStatus.SCHEDULED, VideoStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update video with status '{video.status}'",
        )
    
    # Update fields from input
    update_data = video_in.model_dump(exclude_unset=True)
    
    # Ensure scheduled time is in the future if it's being updated
    if "scheduled_time" in update_data and update_data["scheduled_time"] <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future",
        )
    
    for field, value in update_data.items():
        setattr(video, field, value)
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return video


@router.delete("/{video_id}", response_model=BaseResponse)
def delete_video_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str = Path(..., description="The ID of the video to delete"),
) -> Any:
    """
    Delete a video schedule.
    """
    video = db.query(VideoSchedule).filter(
        VideoSchedule.id == video_id,
        VideoSchedule.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Prevent deletion of videos that are currently being processed
    if video.status == VideoStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a video that is currently being processed",
        )
    
    # Delete the video file if it exists
    if os.path.exists(video.file_path):
        try:
            os.remove(video.file_path)
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error deleting file {video.file_path}: {e}")
    
    # Delete the thumbnail if it exists
    if video.thumbnail_path and os.path.exists(video.thumbnail_path):
        try:
            os.remove(video.thumbnail_path)
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error deleting thumbnail {video.thumbnail_path}: {e}")
    
    db.delete(video)
    db.commit()
    
    return {
        "success": True,
        "message": "Video schedule deleted successfully",
    }


@router.post("/{video_id}/cancel", response_model=VideoResponse)
def cancel_video_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str = Path(..., description="The ID of the video to cancel"),
) -> Any:
    """
    Cancel a scheduled video upload.
    """
    video = db.query(VideoSchedule).filter(
        VideoSchedule.id == video_id,
        VideoSchedule.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Only scheduled videos can be canceled
    if video.status != VideoStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel video with status '{video.status}'",
        )
    
    # Mark as failed with a cancellation message
    video.status = VideoStatus.FAILED
    video.result_message = "Canceled by user"
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return video


@router.post("/{video_id}/thumbnail", response_model=VideoResponse)
async def upload_thumbnail(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str = Path(..., description="The ID of the video"),
    thumbnail_file: UploadFile = File(...),
) -> Any:
    """
    Upload a thumbnail for a video.
    """
    # Check if the file is an image
    allowed_extensions = [".jpg", ".jpeg", ".png"]
    file_extension = os.path.splitext(thumbnail_file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Thumbnail must be one of: {', '.join(allowed_extensions)}",
        )
    
    video = db.query(VideoSchedule).filter(
        VideoSchedule.id == video_id,
        VideoSchedule.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Create user upload directory if it doesn't exist
    user_upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        settings.UPLOAD_DIR,
        current_user.id
    )
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Generate unique filename and save the file
    thumbnail_name = f"thumb_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{file_extension}"
    thumbnail_path = os.path.join(user_upload_dir, thumbnail_name)
    
    # Delete old thumbnail if it exists
    if video.thumbnail_path and os.path.exists(video.thumbnail_path):
        try:
            os.remove(video.thumbnail_path)
        except Exception as e:
            # Log the error but continue with upload
            print(f"Error deleting old thumbnail {video.thumbnail_path}: {e}")
    
    # Save the new thumbnail
    with open(thumbnail_path, "wb") as buffer:
        shutil.copyfileobj(thumbnail_file.file, buffer)
    
    # Update the video record
    video.thumbnail_path = thumbnail_path
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return video

