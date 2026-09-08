"""
Database setup — async engine for the app, sync engine for Alembic.

KEY FIX for sqlalchemy.exc.MissingGreenlet:
  - App uses: postgresql+asyncpg:// (fully async)
  - Alembic uses: postgresql+psycopg2:// (sync, in a thread executor)
  Never call await_only() in a sync context.
"""
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Async engine — used by the FastAPI app
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # Reconnect if connection was dropped
    pool_recycle=3600,    # Recycle connections every hour
    echo=settings.debug,  # SQL logging in debug mode only
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async session per request."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
