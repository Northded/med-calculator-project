from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base
from ..config import settings


engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
)


session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

