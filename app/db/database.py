from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlmodel import SQLModel, Session
from fastapi import Depends
import asyncio
from contextlib import asynccontextmanager
import logging

from app.config.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo_log,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    poolclass=QueuePool
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@asynccontextmanager
async def get_db_context():
    """Provide a database session as an async context manager."""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

async def get_db():
    """Dependency for FastAPI endpoints that need a db session."""
    async with get_db_context() as session:
        yield session

async def create_db_and_tables():
    """Initialize database by creating all tables defined in models."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise 