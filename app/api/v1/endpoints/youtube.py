from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.youtube import exchange_code, get_authorization_url
from app.models.user import User
from app.schemas.base import BaseResponse

router = APIRouter()


@router.get("/authorize", response_model=Dict[str, str])
def authorize_youtube(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a YouTube authorization URL.
    
    This endpoint returns a URL that the user should navigate to in order to
    authorize the application to access their YouTube account.
    """
    # Generate a state parameter for the OAuth2 flow using the user's ID
    state = current_user.id
    
    # Get the authorization URL
    auth_url = get_authorization_url(state=state)
    
    return {
        "url": auth_url,
        "message": "Please navigate to this URL to authorize your YouTube account"
    }


@router.get("/callback", response_model=BaseResponse)
def youtube_callback(
    *,
    db: Session = Depends(get_db),
    code: str = Query(..., description="The authorization code from Google"),
    state: Optional[str] = Query(None, description="The state parameter from the authorization request"),
    error: Optional[str] = Query(None, description="Error message from Google"),
) -> Any:
    """
    Handle the callback from the YouTube authorization flow.
    
    This endpoint is called by Google after the user authorizes the application.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authorization failed: {error}",
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided",
        )
    
    # Find the user by the state parameter (which is the user ID)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No state parameter provided",
        )
    
    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    try:
        # Exchange the authorization code for tokens
        token, refresh_token, expiry = exchange_code(code)
        
        # Save the tokens to the user
        user.youtube_token = token
        user.youtube_refresh_token = refresh_token
        user.youtube_token_expiry = expiry.isoformat()
        
        db.add(user)
        db.commit()
        
        return {
            "success": True,
            "message": "YouTube account successfully connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange authorization code: {str(e)}",
        )

