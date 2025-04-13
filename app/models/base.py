import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseModel(Base):
    """
    Base class for all models.
    
    This abstract base class provides common columns and methods for all models.
    """
    
    __abstract__ = True

    # Use table name derived from class name
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common columns
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        """Return string representation of the model."""
        model_name = self.__class__.__name__
        return f"<{model_name}(id='{self.id}')>"

