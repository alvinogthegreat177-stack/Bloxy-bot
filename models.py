from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from database import Base


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SystemInfo(Base, TimestampMixin):
from sqlalchemy import Boolean
from sqlalchemy import Text


class AIProvider(Base, TimestampMixin):
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    base_url = Column(
        String(500),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )


class AIRequestLog(Base, TimestampMixin):
    __tablename__ = "ai_request_logs"

    id = Column(Integer, primary_key=True, index=True)

    provider = Column(
        String(100),
        nullable=False,
    )

    model = Column(
        String(255),
        nullable=True,
    )

    prompt = Column(
        Text,
        nullable=False,
    )

    response = Column(
        Text,
        nullable=True,
    )

    success = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(255),
        nullable=False,
        default="AI Platform",
    )

    version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
    )
