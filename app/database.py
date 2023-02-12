from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(settings.POSTGRES_USER,
                                                                       settings.POSTGRES_PASSWORD,
                                                                       settings.POSTGRES_HOSTNAME,
                                                                       settings.DATABASE_PORT,
                                                                       settings.POSTGRES_DB)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, echo=True
)
Base = declarative_base()

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with async_session() as db:
        yield db
