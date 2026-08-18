from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
import os

# Convert standard postgres URL to async-compatible format
# postgresql:// -> postgresql+asyncpg://
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "URL"
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
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[drp.ai] Database tables initialized ✅")
