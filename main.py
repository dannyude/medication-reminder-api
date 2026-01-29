import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- DB & AUTH IMPORTS ---
from api.src.database import create_db_and_tables, get_session
from api.src.auth.redis_rate_limiter import init_redis, close_redis
from api.src.notifications.firebase_utils import initialize_firebase

# --- ROUTERS ---
from api.src.users import routes as UserRouters
from api.src.auth import routes as AuthRouters
from api.src.medications import routes as MedicationRouters
from api.src.reminders import routes as ReminderRouters

# --- TASKS (Combined Import) ---
from api.src.reminders.tasks import (
    run_daily_reminder_generation,
    check_and_send_pending_reminders
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediReminder")

scheduler = AsyncIOScheduler()

# The life span of the application
@asynccontextmanager
async def lifespan(_: FastAPI):

    # --- STARTUP ---
    logger.info("🔥 SYSTEM STARTING UP...")

    # 1. Database
    await create_db_and_tables()
    logger.info("✅ Database tables checked.")

    # 2. Redis (CRITICAL FIX)
    try:
        await init_redis()
        logger.info("✅ Redis connection initialized.")
    except Exception as e:
        logger.warning(f"⚠️ Redis failed to start (Rate limiting may be disabled): {e}")

    # 3. Firebase (MOVE THIS UP! ⬆️)
    # We must turn on the notification system BEFORE we start the scheduler
    try:
        initialize_firebase()
        logger.info("✅ Firebase initialized.")
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")

    # 4. Scheduler (START THIS LAST! ⬇️)
    logger.info("⏰ Adding Scheduler Jobs...")

    # Job A: Nightly Refill (Runs at 3 AM)
    scheduler.add_job(
        run_daily_reminder_generation,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_reminder_generation",
        replace_existing=True
    )

    # Job B: Notification Worker
    scheduler.add_job(
        check_and_send_pending_reminders,
        trigger=CronTrigger(minute="*"), # Runs every minute
        id="notification_worker",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started.")

    # Print jobs for debugging
    jobs = scheduler.get_jobs()
    for job in jobs:
        logger.info(f"   -> Job Loaded: {job.id} (Next run: {job.next_run_time})")

    yield

    # --- SHUTDOWN ---
    scheduler.shutdown()
    await close_redis() # <--- CRITICAL FIX: Close Redis cleanly
    logger.info("💤 System shutting down.")



# 4. INITIALIZE APP
app = FastAPI(
    title="Medi Reminder API",
    description="Async FastAPI backend for medication reminders",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
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


# Temporary router to test notifications system
# from api.src.auth.dependencies import get_current_user
# from api.src.users.models import User
# from api.src.notifications.notification_service import NotificationService

# @app.post("/test-notification", tags=["Test"])
# async def trigger_test_notification(
#     user: User = Depends(get_current_user)
# ):
#     """
#     Forces a test notification to the logged-in user immediately.
#     Bypasses the database and scheduler completely.
#     """
#     # 1. Check if user has a token
#     if not user.fcm_token:
#         return {"status": "error", "message": "You have no FCM Token!"}

#     # 2. Send the push
#     success = await NotificationService.send_push_notification(
#         token=user.fcm_token,
#         title="🧪 Test Notification",
#         body="If you can read this, the system works!",
#         data={"type": "test"}
#     )

#     if success:
#         return {"status": "success", "message": "Notification sent!"}
#     else:
#         return {"status": "failed", "message": "Firebase rejected the request."}