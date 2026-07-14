"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .models import Base
from src.config import config
from src.utils import get_logger

logger = get_logger(__name__)


def create_db_engine():
    """Create database engine."""
    if config.database.sqlite_path.startswith("postgresql://"):
        db_url = config.database.sqlite_path
        logger.info(f"Creating database engine for PostgreSQL: {db_url.split('@')[1] if '@' in db_url else 'Unknown'}")
        
        engine = create_engine(
            db_url,
            echo=config.database.echo,
            pool_size=10,
            max_overflow=20
        )
    else:
        # Default fallback strictly to sqlite
        db_url = f"sqlite:///{config.database.sqlite_path}" if not config.database.sqlite_path.startswith("sqlite") else config.database.sqlite_path
        logger.info(f"Creating database engine: {db_url}")
        
        engine = create_engine(
            db_url,
            echo=config.database.echo,
            poolclass=StaticPool,  # Use static pool for SQLite
            connect_args={"check_same_thread": False}
        )
    
    return engine


def init_db():
    """Initialize database tables."""
    engine = create_db_engine()
    logger.info("Initializing database tables")
    Base.metadata.create_all(engine)
    return engine


# Create engine and session factory
engine = None
SessionLocal = None


def get_session() -> Session:
    """Get database session."""
    global engine, SessionLocal
    
    if engine is None:
        engine = init_db()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def close_db():
    """Close database connection."""
    global engine, SessionLocal
    if engine:
        engine.dispose()
        logger.info("Database connection closed")
