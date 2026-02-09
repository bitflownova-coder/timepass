"""
Database management for Copilot Engine
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from models import Base
from config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database manager"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(settings.db_path)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_db(self) -> Session:
        """Get database session (for FastAPI dependency)"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Global database instance
db = Database()
