from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass
# Dependency for FastAPI routes


# # @contextmanager
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
