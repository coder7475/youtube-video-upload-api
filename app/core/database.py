from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    # For SQLite, we need to enable foreign key constraints explicitly
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency
def get_db() -> Generator:
    """
    Get database session.
    
    This function is used as a FastAPI dependency to provide
    a database session to API endpoint functions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

