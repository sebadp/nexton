"""
Database connection and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
# Create async engine
if not settings.DATABASE_URL:
    # If no database URL, we can't create an engine.
    # We'll log a warning and set engine to None.
    # This avoids crashing on import, but will fail if DB is accessed.
    # Useful for running scripts or tests that mock DB.
    import logging
    from typing import Any

    logging.getLogger(__name__).warning(
        "DATABASE_URL is not set. Database features will be unavailable."
    )
    engine = None
    AsyncSessionLocal: Any = None

    class DummySession:
        """Dummy session that raises error when called."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError("Database not configured (DATABASE_URL missing)")

        async def __aenter__(self):
            raise RuntimeError("Database not configured (DATABASE_URL missing)")

        async def __aexit__(self, *args):
            pass

    AsyncSessionLocal = DummySession
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured (DATABASE_URL missing)")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    Only use in development/testing.
    In production, use Alembic migrations.
    """
    if engine is None:
        raise RuntimeError("Database not configured (DATABASE_URL missing)")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    if engine:
        await engine.dispose()
