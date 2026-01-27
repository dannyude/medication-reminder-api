import logging
from datetime import datetime, timedelta, timezone as dt_timezone, time
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.src.medications.models import Medication, FrequencyType
from api.src.reminders.models import Reminder, ReminderStatus

logger = logging.getLogger(__name__)


class ReminderGenerator:
    """Generate reminders for medications efficiently."""

    @staticmethod
    async def generate_reminders_for_medication(
        session: AsyncSession,
        medication: Medication,
        days_ahead: int = 7
    ) -> list[Reminder]:

        if not medication.is_active:
            return []

        # 1. Define the Time Window
        now_utc = datetime.now(dt_timezone.utc)
        end_generation = now_utc + timedelta(days=days_ahead)

        # Cap generation at the medication's end date (if it exists)
        # Note: Ensure to compare datetime vs datetime
        if medication.end_datetime and medication.end_datetime < end_generation:
            end_generation = medication.end_datetime

        # 2. OPTIMIZATION: Fetch ALL existing reminders in this window ONCE
        # This prevents running thousands of "Select" queries in the loop
        existing_stmt = select(Reminder.scheduled_time).where(
            and_(
                Reminder.medication_id == medication.id,
                Reminder.scheduled_time >= now_utc,
                Reminder.scheduled_time <= end_generation
            )
        )
        existing_result = await session.execute(existing_stmt)

        # Create a "Lookup Set" for instant checking
        existing_reminders = {dt for dt in existing_result.scalars().all()}

        reminders: list[Reminder] = []

        # 3. Route to logic
        if medication.frequency_type in {
            FrequencyType.ONCE_DAILY, FrequencyType.TWICE_DAILY,
            FrequencyType.THREE_TIMES_DAILY, FrequencyType.FOUR_TIMES_DAILY,
        }:
            times_map = {
                FrequencyType.ONCE_DAILY: [time(8, 0)],
                FrequencyType.TWICE_DAILY: [time(8, 0), time(20, 0)],
                FrequencyType.THREE_TIMES_DAILY: [time(8, 0), time(14, 0), time(20, 0)],
                FrequencyType.FOUR_TIMES_DAILY: [time(8, 0), time(12, 0), time(16, 0), time(20, 0)],
            }
            # Use default if type not found (fallback)
            schedule_times = times_map.get(medication.frequency_type, [time(8, 0)])

            reminders = ReminderGenerator._generate_daily_reminders(
                medication, now_utc, end_generation, schedule_times, existing_reminders
            )

        elif medication.frequency_type == FrequencyType.EVERY_X_HOURS:
            reminders = ReminderGenerator._generate_interval_reminders(
                medication, now_utc, end_generation, existing_reminders
            )

        return reminders

    # DAILY REMINDERS
    @staticmethod
    def _generate_daily_reminders(
        medication: Medication,
        start_utc: datetime,
        end_utc: datetime,
        dose_times: list[time],
        existing_reminders: set[datetime]
    ) -> list[Reminder]:
        """
        Generates reminders based on wall-clock time (e.g. always 8 AM local).
        """
        reminders: list[Reminder] = []

        # Guard against invalid timezones
        try:
            tz = ZoneInfo(medication.timezone)
        except Exception:
            tz = dt_timezone.utc

        # Convert start/end UTC window to Local Dates
        current_date = start_utc.astimezone(tz).date()
        end_date = end_utc.astimezone(tz).date()

        while current_date <= end_date:
            for dose_time in dose_times:
                # 1. Construct Local Time (e.g., "Jan 25th at 8:00 PM Lagos Time")
                local_dt = datetime.combine(current_date, dose_time, tzinfo=tz)

                # 2. Convert to UTC for storage
                scheduled_utc = local_dt.astimezone(dt_timezone.utc)

                # 3. Validation Checks
                if scheduled_utc < start_utc: continue
                if scheduled_utc > end_utc: continue

                # 4. FAST CHECK: Check against the Set (O(1) complexity)
                if scheduled_utc in existing_reminders:
                    continue

                reminders.append(
                    Reminder(
                        medication_id=medication.id,
                        user_id=medication.user_id,
                        scheduled_time=scheduled_utc,
                        status=ReminderStatus.PENDING
                    )
                )

            current_date += timedelta(days=1)

        return reminders

    # INTERVAL REMINDERS
    @staticmethod
    def _generate_interval_reminders(
        medication: Medication,
        start_utc: datetime,
        end_utc: datetime,
        existing_reminders: set[datetime]
    ) -> list[Reminder]:

        if not medication.frequency_value:
            return []

        reminders: list[Reminder] = []
        interval = timedelta(hours=medication.frequency_value)

        # Use medication start datetime
        current = medication.start_datetime

        # "Fast Forward" logic:
        # Jump from the medication start date to the current window
        # This keeps the grid aligned (e.g., 8am, 4pm, 12am) even months later
        if current < start_utc:
            delta = start_utc - current
            steps = int(delta.total_seconds() // interval.total_seconds())
            current += interval * steps

            # Ensure we are actually *inside* or *after* the start window
            if current < start_utc:
                current += interval

        while current <= end_utc:
            if current not in existing_reminders:
                reminders.append(
                    Reminder(
                        medication_id=medication.id,
                        user_id=medication.user_id,
                        scheduled_time=current,
                        status=ReminderStatus.PENDING
                    )
                )

            current += interval

        return reminders

    # BATCH GENERATION
    @staticmethod
    async def generate_all_upcoming_reminders(
        session: AsyncSession,
        days_ahead: int = 7
    ) -> int:

        # Select active meds
        stmt = select(Medication).where(Medication.is_active.is_(True))
        result = await session.execute(stmt)
        medications = result.scalars().all()

        total_created = 0

        for med in medications:
            new_reminders = await ReminderGenerator.generate_reminders_for_medication(
                session, med, days_ahead
            )
            if new_reminders:
                session.add_all(new_reminders)
                total_created += len(new_reminders)

        if total_created > 0:
            await session.commit()
            logger.info(f"✅ Created {total_created} new reminders.")

        return total_created