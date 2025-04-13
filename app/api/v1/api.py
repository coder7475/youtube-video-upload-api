from fastapi import APIRouter

from app.api.v1.endpoints import auth, videos, youtube

api_router = APIRouter()

# Include API routers
api_router.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
api_router.include_router(youtube.router, prefix="/v1/youtube", tags=["youtube"])
api_router.include_router(videos.router, prefix="/v1/videos", tags=["videos"])

