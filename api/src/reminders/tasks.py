import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload

from api.src.database import async_session

from api.src.reminders.reminder_generator import ReminderGenerator
from api.src.reminders.models import Reminder, ReminderStatus

from api.src.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)

# --- JOB 1: The Nightly Factory (Runs once a day) ---
async def run_daily_reminder_generation():
    """
    Nightly task to refill reminders for the next 7 days.
    """
    logger.info("🏭 Starting nightly reminder generation task...")

    async with async_session() as session:
        try:
            total = await ReminderGenerator.generate_all_upcoming_reminders(
                session=session,
                days_ahead=7
            )
            logger.info("✅ Nightly Task Complete: Generated: %s reminders.", total)
        except Exception as e:
            logger.error("❌ Nightly Generation Failed: %s", str(e), exc_info=True)


# --- JOB 2: The Reminder Dispatcher (Runs every minute) ---
async def check_and_send_pending_reminders():
    """
    1. Finds reminders that are DUE (scheduled_time <= now) and PENDING.
    2. Sends them using NotificationService.
    3. Marks them as SENT.
    """
    # Define "Now" and the "Cutoff" (e.g., 15 mins ago)
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(minutes=15)

    async with async_session() as session:
        try:
            # 🧹 STEP 1: Mark Stale/Old Reminders as MISSED
            # If the server was down, or the cron didn't run, we don't want to send a reminder
            # that is 15 minutes late. Just mark it missed.
            stale_query = (
                update(Reminder)
                .where(
                    and_(
                        Reminder.status == ReminderStatus.PENDING,
                        Reminder.scheduled_time < cutoff_time
                    )
                )
                .values(status=ReminderStatus.MISSED)
            )
            await session.execute(stale_query)
            # We commit immediately so the DB is clean for the next step
            await session.commit()

            # Fetch Only Valid, Recent Reminders
            # We use 'selectinload' to grab User & Med info efficiently in one go.
            query = (
                select(Reminder)
                .where(
                    and_(
                        Reminder.status == ReminderStatus.PENDING,
                        Reminder.scheduled_time <= now
                    )
                )
                .options(
                    selectinload(Reminder.user),      # Load User (for token/phone)
                    selectinload(Reminder.medication) # Load Med (for name/dosage)
                )
            )

            result = await session.execute(query)
            due_reminders = result.scalars().all()

            if not due_reminders:
                # logger.info("😴 No pending reminders found.") # Optional: Reduce log spam
                return

            logger.info("🔔 Found %d due reminders. Processing...", len(due_reminders))

            # Process & Send
            for reminder in due_reminders:
                try:
                    # Trigger the Notification Service
                    # (Handles Push -> SMS Fallback internally)
                    success = await NotificationService.send_reminder_notification(reminder, session)

                    if success:
                        reminder.status = ReminderStatus.SENT
                        reminder.notification_sent_at = datetime.now(timezone.utc)
                        logger.info("✅ Reminder %d marked as SENT.", reminder.id)
                    else:
                        # If both Push and SMS failed, we keep it PENDING to retry
                        # OR you can mark it FAILED if you don't want retries.
                        logger.warning("⚠️ Failed to send reminder %d. Keeping as PENDING.", reminder.id)
                except Exception as e:
                    logger.error("❌ Error processing reminder %d: %s", reminder.id, str(e))

            # Save All Changes
            await session.commit()

        except Exception as e:
            logger.error("❌ Critical Error in Reminder Task: %s", str(e), exc_info=True)
            await session.rollback()