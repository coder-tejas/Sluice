from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def get_async_url() -> str:
    url = str(get_settings().database_url)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://","postgresql+asyncpg://",1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://","postgresql+asyncpg://",1)
    return url

async_engine = create_async_engine(
    get_async_url(),
    pool_pre_ping = True,
    pool_size = 5,
    max_overflow = 10
)
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,class_ = AsyncSession,expire_on_commit = False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

async def check_async_connection() -> int:
    async with async_engine.connect() as conn:
        return (await conn.execute(text("SELECT 1"))).scalar()