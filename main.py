from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.src.database import create_db_and_tables, get_session
from api.src.auth.redis_rate_limiter import init_redis, close_redis

from api.src.users import routes as UserRouters
from api.src.auth import routes as AuthRouters
from api.src.medications import routes as MedicationRouters
from api.src.reminders import routes as ReminderRouters


# The life span of the application
@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Docstring for lifespan

    :The Start up logic
    """
    print("🚀 Starting up...")
    await create_db_and_tables()
    print("✅ Database tables checked.")

    await init_redis()

    yield


    # Shutdown Logic
    print("🛑 Shutting down...")
    await close_redis()
    print("✅ Redis connection closed.")

app = FastAPI(
    title="Medi Reminder API",
    description="Async FastAPI backend for medication reminders",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(UserRouters.router, tags=["Users"])
app.include_router(AuthRouters.router, tags=["Authentication"])
app.include_router(MedicationRouters.router, tags=["Medications"])
app.include_router(ReminderRouters.router, tags=["Reminders"])


@app.get("/health", tags=["Health"])
async def health_check(session: AsyncSession = Depends(get_session)):
    """
    Deep Health Check.
    Verifies that the API is running AND the Database is accessible.
    """
    try:
        # Tries to execute a simple SQL query to verify connection
        await session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "online",
            "service": "Medi Reminder API"
        }
    except Exception as e:
        # If DB is down, return 503 so load balancers stop sending traffic
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        ) from e