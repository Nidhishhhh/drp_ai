"""
drp.ai — database/session.py
Async SQLAlchemy session management.
Import get_db in FastAPI routes as a dependency.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
import os

# Convert standard postgres URL to async-compatible format
# postgresql:// -> postgresql+asyncpg://
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_aqgw4hAX2xRj@ep-dawn-surf-aokt6ql5.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
).replace("postgresql://", "postgresql+asyncpg://").replace("?sslmode=require", "")

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    connect_args={"ssl": True},  # pass SSL this way for asyncpg
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields an async database session.

    Usage in routes:
        from database.session import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        from fastapi import Depends

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """
    Creates all tables on startup if they don't exist.
    Called from main.py lifespan.
    """
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[drp.ai] Database tables initialized ✅")