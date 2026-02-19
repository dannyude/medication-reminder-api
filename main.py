import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import FileResponse

# --- DB & AUTH IMPORTS ---
from api.src.database import create_db_and_tables, get_session
from api.src.auth.redis_rate_limiter import init_redis, close_redis
from api.src.notifications.firebase_utils import initialize_firebase

# --- ROUTERS ---
from api.src.users import routes as UserRouters
from api.src.auth import routes as AuthRouters
from api.src.medications import routes as MedicationRouters
from api.src.reminders import routes as ReminderRouters
from api.src.logs import routes as LogRouters
from api.src.config_package import routes as ConfigRouters
from api import cron as CronRouter

from api.src.config_package.settings import settings

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediReminder")

# Parse CORS origins from settings
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
if settings.ENVIRONMENT == "development":
    cors_origins.extend(["*"])

logger.info("CORS Origins: %s", cors_origins)

# The life span of the application
@asynccontextmanager
async def lifespan(_: FastAPI):

    # --- STARTUP ---
    logger.info("🔥 API SYSTEM STARTING UP...")

    # 1. Database
    await create_db_and_tables()
    logger.info("✅ Database tables checked.")

    # 2. Redis
    try:
        await init_redis()
        logger.info("✅ Redis connection initialized.")
    except Exception as e:
        logger.warning("⚠️ Redis failed to start (Rate limiting may be disabled): %s", e)

    # 3. Firebase
    try:
        initialize_firebase()
        logger.info("✅ Firebase initialized.")
    except Exception as e:
        logger.error("❌ Firebase initialization failed: %s", e)

    yield

    # --- SHUTDOWN ---
    await close_redis() # Ensure Redis connection is closed properly
    logger.info("💤 API System shutting down.")


# 4. INITIALIZE APP
app = FastAPI(
    title="Medi Reminder API",
    description="Async FastAPI backend for medication reminders.",
    version="1.0.0",  # "1.0.0" is often preferred over "v1" for semantic versioning
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Be explicit, not "*"
    allow_headers=["Content-Type", "Authorization"],  # Be explicit, not "*"
)

# Routers
app.include_router(UserRouters.router)
app.include_router(AuthRouters.router)
app.include_router(MedicationRouters.router)
app.include_router(ReminderRouters.router)
app.include_router(LogRouters.router)
app.include_router(ConfigRouters.router)
app.include_router(CronRouter.router)

# Serve static files (for testing Google OAuth)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

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
            "service": "Medi Reminder API (Workerless Mode)"
        }
    except Exception as e:
        # If DB is down, return 503 so load balancers stop sending traffic
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        ) from e

@app.get("/firebase-messaging-sw.js", include_in_schema=False)
async def service_worker():
    # Make sure the path points to where your file actually is!
    return FileResponse("frontend/firebase-messaging-sw.js")

# 2. (Optional) If you serve other static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")