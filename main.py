from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.src.database import create_db_and_tables
from api.src.auth.redis_rate_limiter import init_redis, close_redis
from api.src.users import routes as UserRouters
from api.src.auth import routes as AuthRouters
from api.src.medications import routes as MedicationRouters

# The life span of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
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