import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import config

Base = declarative_base()

# Database setup
DATABASE_URL = config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_recycle=300,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    from models import User, Subscription, Usage, WatermarkSettings
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

def get_db_session():
    """Get a database session for direct use."""
    return SessionLocal()
