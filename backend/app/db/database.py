"""
Database configuration and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from app.core.logging import log

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://step_admin:step_secure_pass_2024@postgres:5432/step_cad_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    log.info("database_initialization_started")
    try:
        Base.metadata.create_all(bind=engine)
        log.info("database_tables_created_successfully")
    except Exception as e:
        log.error("database_initialization_failed", error=str(e))
        raise


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        log.error("database_connection_check_failed", error=str(e))
        return False
