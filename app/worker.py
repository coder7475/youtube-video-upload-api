import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.youtube import refresh_token, upload_video
from app.models.user import User
from app.models.video import VideoSchedule, VideoStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "youtube_scheduler",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Add periodic tasks
celery_app.conf.beat_schedule = {
    'check-scheduled-videos-every-minute': {
        'task': 'app.worker.check_scheduled_videos',
        'schedule': crontab(minute='*'),  # Run every minute
    },
}

# Setup database connection
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Create a new database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@celery_app.task(
    name="app.worker.upload_youtube_video",
    bind=True,
    max_retries=3,
    soft_time_limit=3600,  # 1 hour
    time_limit=7200,  # 2 hours (for large videos)
)
def upload_youtube_video(self, video_id: str):
    """
    Celery task to upload a video to YouTube.
    
    Args:
        video_id: The ID of the VideoSchedule to upload.
    """
    db = get_db()
    
    try:
        # Get the video schedule
        video = db.query(VideoSchedule).filter(VideoSchedule.id == video_id).first()
        if not video:
            logger.error(f"Video with ID {video_id} not found")
            return False
        
        # Get the user
        user = db.query(User).filter(User.id == video.user_id).first()
        if not user:
            logger.error(f"User with ID {video.user_id} not found")
            video.status = VideoStatus.FAILED
            video.result_message = "User not found"
            db.add(video)
            db.commit()
            return False
        
        # Check if the user has YouTube credentials
        if not user.youtube_token or not user.youtube_refresh_token:
            logger.error(f"User {user.id} doesn't have YouTube credentials")
            video.status = VideoStatus.FAILED
            video.result_message = "YouTube credentials not found"
            db.add(video)
            db.commit()
            return False
        
        # Check if the token needs to be refreshed
        token_expiry = datetime.fromisoformat(user.youtube_token_expiry) if user.youtube_token_expiry else None
        if not token_expiry or token_expiry <= datetime.utcnow():
            logger.info(f"Refreshing token for user {user.id}")
            success = refresh_token(user, db)
            if not success:
                logger.error(f"Failed to refresh token for user {user.id}")
                video.status = VideoStatus.FAILED
                video.result_message = "Failed to refresh YouTube token"
                db.add(video)
                db.commit()
                return False
        
        # Upload the video
        try:
            logger.info(f"Uploading video {video.id} to YouTube")
            response = upload_video(video, user, db)
            logger.info(f"Video {video.id} uploaded successfully: {response['id']}")
            return True
        except Exception as upload_error:
            logger.error(f"Error uploading video {video.id}: {str(upload_error)}")
            # If this is a quota error, retry after a delay
            if "quota" in str(upload_error).lower():
                logger.warning("YouTube quota exceeded, will retry later")
                # Retry after 1 hour with exponential backoff
                retry_in = 3600 * (2 ** self.request.retries)
                self.retry(exc=upload_error, countdown=retry_in)
            # Otherwise, mark as failed
            video.status = VideoStatus.FAILED
            video.result_message = f"Upload failed: {str(upload_error)}"
            db.add(video)
            db.commit()
            return False
    
    except Exception as e:
        logger.exception(f"Unexpected error in upload_youtube_video task: {str(e)}")
        try:
            # Attempt to update the video status
            video = db.query(VideoSchedule).filter(VideoSchedule.id == video_id).first()
            if video:
                video.status = VideoStatus.FAILED
                video.result_message = f"Unexpected error: {str(e)}"
                db.add(video)
                db.commit()
        except Exception:
            pass
        
        # Retry the task with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        db.close()


@celery_app.task(name="app.worker.check_scheduled_videos")
def check_scheduled_videos():
    """
    Check for videos scheduled to be uploaded in the next 15 minutes.
    
    This task runs periodically to find videos that are due for upload
    and triggers the upload task for each one.
    """
    db = get_db()
    
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Find videos scheduled to be uploaded in the next 15 minutes
        # that are still in SCHEDULED status
        videos = (
            db.query(VideoSchedule)
            .filter(
                VideoSchedule.status == VideoStatus.SCHEDULED,
                VideoSchedule.scheduled_time <= now + timedelta(minutes=15),
                VideoSchedule.scheduled_time > now - timedelta(minutes=60),  # Don't process videos more than 1 hour late
            )
            .all()
        )
        
        logger.info(f"Found {len(videos)} videos scheduled for upload")
        
        # Trigger upload tasks for each video
        for video in videos:
            # Update status to PENDING
            video.status = VideoStatus.PENDING
            video.result_message = f"Upload scheduled at {now.isoformat()}"
            db.add(video)
            db.commit()
            
            # Trigger the upload task
            upload_youtube_video.apply_async(args=[video.id])
            
            logger.info(f"Scheduled upload for video {video.id}")
        
        return len(videos)
    
    except Exception as e:
        logger.exception(f"Error in check_scheduled_videos task: {str(e)}")
        return 0
    
    finally:
        db.close()


@celery_app.task(name="app.worker.retry_failed_uploads")
def retry_failed_uploads():
    """
    Retry failed video uploads.
    
    This task looks for videos that failed to upload and retries them.
    It should be run less frequently, e.g., once or twice a day.
    """
    db = get_db()
    
    try:
        # Find videos that failed to upload
        videos = (
            db.query(VideoSchedule)
            .filter(
                VideoSchedule.status == VideoStatus.FAILED,
                VideoSchedule.scheduled_time > datetime.utcnow() - timedelta(days=7)  # Only retry videos from the last week
            )
            .all()
        )
        
        logger.info(f"Found {len(videos)} failed uploads to retry")
        
        # Trigger upload tasks for each video
        for video in videos:
            # Update status to PENDING
            video.status = VideoStatus.PENDING
            video.result_message = f"Retrying upload at {datetime.utcnow().isoformat()}"
            db.add(video)
            db.commit()
            
            # Trigger the upload task
            upload_youtube_video.apply_async(args=[video.id])
            
            logger.info(f"Retrying upload for video {video.id}")
        
        return len(videos)
    
    except Exception as e:
        logger.exception(f"Error in retry_failed_uploads task: {str(e)}")
        return 0
    
    finally:
        db.close()


# Add periodic task for retrying failed uploads
celery_app.conf.beat_schedule['retry-failed-uploads-daily'] = {
    'task': 'app.worker.retry_failed_uploads',
    'schedule': crontab(hour=3, minute=0),  # Run at 3:00 AM UTC every day
}

