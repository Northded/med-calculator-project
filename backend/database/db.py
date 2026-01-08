import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import OperationalError
from .models import Base
from ..config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
)

session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

async def get_session():
    async with session_factory() as session:
        yield session

async def create_db():
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Попытка подключения к БД ({attempt}/{max_retries})...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("База данных готова")
            return
        except (OperationalError, ConnectionRefusedError, OSError) as e:
            if attempt < max_retries:
                logger.warning(f"Не удалось подключиться, жду {retry_delay} сек...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Не удалось подключиться к БД!")
                raise
