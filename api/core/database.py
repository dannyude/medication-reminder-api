from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from .config import settings


#Get the DATABASE URL
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DB_URL not set in .env or config")

# Crete the async engine   
engine = create_async_engine(DATABASE_URL, echo=True)

#Create the async session maker
async_session: sessionmaker[AsyncSession] = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
    )

# ceate the base class for all models
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
    """
    FastAPI dependency to get an async database session.
    Yields a session, rolls back on SQLAlchemy errors, and always closes the session.
    """
    session = async_session()
    
    try:
        yield session
    except SQLAlchemyError:
        await session.rollback()
        raise
    finally:
        await session.close()