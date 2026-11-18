"""Database engine configuration; schema and migrations are deferred."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Yield a short-lived database session for an API request."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
