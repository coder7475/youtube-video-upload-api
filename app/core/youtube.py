import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.video import VideoSchedule, VideoStatus


# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".client_secrets.json")

# YouTube API scopes
SCOPES = settings.GOOGLE_AUTH_SCOPES.split()
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def get_authorization_url(state: Optional[str] = None) -> str:
    """
    Get the authorization URL for the OAuth2 flow.
    
    Args:
        state: Optional state parameter for the OAuth2 flow.
        
    Returns:
        str: The authorization URL.
    """
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console.
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    # Generate URL for request to Google's OAuth 2.0 server.
    authorization_url, _ = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission
        access_type='offline',
        # Enable incremental authorization
        include_granted_scopes='true',
        # Force to always prompt for consent
        prompt='consent',
        # Optional state
        state=state
    )

    return authorization_url


def exchange_code(code: str) -> Tuple[str, str, datetime]:
    """
    Exchange an authorization code for OAuth 2.0 credentials.
    
    Args:
        code: The authorization code to exchange.
        
    Returns:
        Tuple[str, str, datetime]: A tuple containing the access token,
                                  refresh token, and expiry time.
    """
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    flow.fetch_token(code=code)

    # Save credentials for the current user
    credentials = flow.credentials
    
    # Calculate expiry time
    expiry = datetime.utcnow() + timedelta(seconds=credentials.expires_in)
    
    return credentials.token, credentials.refresh_token, expiry


def get_youtube_client(user: User) -> googleapiclient.discovery.Resource:
    """
    Get an authenticated YouTube API client for a user.
    
    Args:
        user: The user to get the YouTube client for.
        
    Returns:
        googleapiclient.discovery.Resource: The YouTube API client.
        
    Raises:
        ValueError: If the user doesn't have YouTube credentials.
    """
    if not user.youtube_token:
        raise ValueError("User doesn't have YouTube credentials")
    
    # Create credentials from stored tokens
    credentials = google.oauth2.credentials.Credentials(
        token=user.youtube_token,
        refresh_token=user.youtube_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES
    )
    
    # Build the API client
    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials,
        cache_discovery=False
    )
    
    return youtube


def refresh_token(user: User, db: Session) -> bool:
    """
    Refresh a user's YouTube access token.
    
    Args:
        user: The user to refresh the token for.
        db: The database session.
        
    Returns:
        bool: True if the token was refreshed successfully, False otherwise.
    """
    try:
        # Create credentials from stored tokens
        credentials = google.oauth2.credentials.Credentials(
            token=user.youtube_token,
            refresh_token=user.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )
        
        # Refresh the token
        credentials.refresh(Request())
        
        # Update the user's tokens
        user.youtube_token = credentials.token
        user.youtube_token_expiry = (datetime.utcnow() + 
                                    timedelta(seconds=credentials.expires_in)).isoformat()
        
        db.add(user)
        db.commit()
        
        return True
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return False


def upload_video(video: VideoSchedule, user: User, db: Session) -> Dict[str, Any]:
    """
    Upload a video to YouTube.
    
    Args:
        video: The video schedule to upload.
        user: The user who owns the video.
        db: The database session.
        
    Returns:
        Dict[str, Any]: The response from the YouTube API.
        
    Raises:
        Exception: If the upload fails.
    """
    # Update video status to processing
    video.status = VideoStatus.PROCESSING
    db.add(video)
    db.commit()
    
    try:
        # Get the YouTube client
        youtube = get_youtube_client(user)
        
        # Prepare the request body
        body = {
            "snippet": {
                "title": video.title,
                "description": video.description or "",
                "tags": video.tags.split(",") if video.tags else [],
                "categoryId": video.category_id or "22"  # Default to "People & Blogs"
            },
            "status": {
                "privacyStatus": video.privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Create a MediaFileUpload object for the video file
        media = MediaFileUpload(
            video.file_path,
            mimetype="video/*",
            resumable=True
        )
        
        # Call the API's videos.insert method to upload the video
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        # Execute the upload
        response = insert_request.execute()
        
        # Update the video with the response
        video.youtube_video_id = response["id"]
        video.status = VideoStatus.UPLOADED
        video.result_message = f"Successfully uploaded to YouTube with ID: {response['id']}"
        
        # If there's a thumbnail, upload it
        if video.thumbnail_path:
            try:
                youtube.thumbnails().set(
                    videoId=response["id"],
                    media_body=MediaFileUpload(video.thumbnail_path)
                ).execute()
            except Exception as thumb_err:
                video.result_message += f" (Thumbnail upload failed: {str(thumb_err)})"
        
        db.add(video)
        db.commit()
        
        return response
    except Exception as e:
        # Update the video status to failed
        video.status = VideoStatus.FAILED
        video.result_message = f"Upload failed: {str(e)}"
        db.add(video)
        db.commit()
        
        # Re-raise the exception
        raise

