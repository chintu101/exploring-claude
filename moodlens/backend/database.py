"""
database.py
───────────
Async SQLAlchemy engine and session factory.
Uses SQLite for hackathon portability; swap DATABASE_URL to
PostgreSQL in production without touching application code.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite-specific: required for async multi-thread safety
    connect_args={"check_same_thread": False},
)

# ── Session factory ────────────────────────────────────────────────────────
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Base for all ORM models ────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Declarative base class. All models inherit from this."""
    pass


# ── FastAPI dependency ─────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session per request.
    Rolls back on unhandled exceptions; always closes the session.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables (called once on startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
