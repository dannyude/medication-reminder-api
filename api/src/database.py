from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.src.config import settings


# Get the DATABASE URL
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DB_URL not set in .env or config")

# Crete the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create the async session maker
async_session: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
    ) # type: ignore

# Create the base class for all models
Base = declarative_base()

# Function to create database tables
async def create_db_and_tables() -> None:
    """
    Creates all tables defined in models that inherit from Base.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
# Async dependency to get a session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            #await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise