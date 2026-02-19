import os
import logging
import secrets
from fastapi import APIRouter, Header, HTTPException


# Import the exact same function your scheduler was using!
from api.src.reminders.tasks import check_and_send_pending_reminders

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])

@router.post("/cron/run-reminders")
async def run_reminders_cron(cron_secret: str | None = Header(default=None, alias="x-cron-secret")):
    """
    This endpoint is called every 1 minute by cron-job.org.
    """
    # 1. Security Check (So random people on the internet can't trigger it)
    expected_secret = os.getenv("CRON_SECRET")
    if not expected_secret:
        logger.error("CRON_SECRET is not configured")
        raise HTTPException(status_code=500, detail="Cron is not configured")

    if not cron_secret or not secrets.compare_digest(cron_secret, expected_secret):
        logger.warning("Unauthorized cron attempt!")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. Call your existing logic!
    logger.info("External cron triggered! Checking reminders...")
    await check_and_send_pending_reminders()

    return {"status": "success", "message": "Reminders checked successfully."}