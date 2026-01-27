import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.src.medications.models import Medication, Reminder, FrequencyType, ReminderStatus
from api.src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ReminderService:

    @staticmethod
    async def generate_reminders_for_medication(
        session: AsyncSession,
        medication: Medication,
        days_ahead: int = 7
    ):
        """Generate reminders for a medication for the next X days."""

        # Implementation based on frequency_type
        # This generates reminder records in the database
        pass

    @staticmethod
    async def check_and_send_reminders(session: AsyncSession):
        """
        Background task to check and send pending reminders.
        Run this every minute via Celery or APScheduler.
        """

        now = datetime.now(timezone.utc)

        # Get pending reminders that should be sent now
        stmt = select(Reminder).where(
            and_(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.scheduled_time <= now,
                Reminder.scheduled_time >= now - timedelta(minutes=5)
            )
        )

        result = await session.execute(stmt)
        reminders = result.scalars().all()

        for reminder in reminders:
            try:
                # Send notification (SMS/Push/Email)
                await NotificationService.send_reminder(reminder)

                reminder.status = ReminderStatus.SENT
                reminder.notification_sent_at = now

                logger.info(f"Reminder sent for medication {reminder.medication_id}")

            except Exception as e:
                logger.error(f"Failed to send reminder: {str(e)}")

        await session.commit()