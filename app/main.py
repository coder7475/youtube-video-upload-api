import time
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1.api import api_router
from app.core.config import settings
from app.models.base import Base
from app.core.database import engine

# Create database tables (if using SQLite)
# In production with migrations, this shouldn't be necessary
if settings.DEBUG and settings.DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=None,  # We'll customize the docs path
    redoc_url=None,  # We'll customize the redoc path
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with a clean response."""
    errors = []
    for error in exc.errors():
        errors.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "message": "Validation error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent formatting."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": str(exc.detail)},
    )


# Simple request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "app_name": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION, 
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "health_check": "/health"
    }


# Custom docs routes
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation."""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok", 
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


# Uploads directory for static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

