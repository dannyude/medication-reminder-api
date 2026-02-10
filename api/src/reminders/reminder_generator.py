import logging
from datetime import datetime, timedelta, timezone as dt_timezone, time
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.src.medications.models import Medication, FrequencyType
from api.src.reminders.models import Reminder, ReminderStatus

logger = logging.getLogger(__name__)


class ReminderGenerator:
    """
    Generates medication reminders efficiently for all frequency types.
    Handles timezone conversions, duplicate prevention, and batch operations.

    Key concepts:
    - Reminders are only created for active medications
    - Existing reminders are checked to prevent duplicates
    - All timestamps are normalized to UTC for consistency
    - Timezone awareness prevents DST/scheduling issues
    """

    @staticmethod
    async def generate_reminders_for_medication(
        session: AsyncSession,
        medication: Medication,
        days_ahead: int = 30
    ) -> list[Reminder]:
        """
        Generate reminders for a single medication based on its frequency type.
        Returns list of Reminder objects (not yet committed to DB).

        Args:
            session: Async database session
            medication: Medication record to generate reminders for
            days_ahead: Number of days to generate reminders (default 30)

        Returns:
            List of Reminder objects ready for batch insert

        Troubleshooting:
            - Inactive medications: Check is_active flag if reminders stop appearing
            - Expired medications: Medication with end_datetime in past are skipped
            - Invalid timezone: Falls back to UTC if timezone string is invalid
            - Invalid reminder_times: Non-ISO format times are logged as warnings
            - Duplicates: Verify only one scheduler instance running, check DB transactions
            - Timestamp mismatches: All timestamps must have microsecond=0 for duplicate detection
            - Missing reminders: Check medication.start_datetime and end_datetime boundaries
        """

        # Inactive medications generate no reminders.
        if not medication.is_active:
            return []

        # Get current time in UTC with no microseconds (for consistent matching).
        now_utc = datetime.now(dt_timezone.utc).replace(microsecond=0)

        # Expired medications are skipped.
        if medication.end_datetime and medication.end_datetime <= now_utc:
            logger.info("⏭️ Skipping %s: End date %s has passed.", medication.name, medication.end_datetime)
            return []

        # Reminders never start before medication start_datetime.
        start_point = max(now_utc, medication.start_datetime).replace(microsecond=0)

        # Calculate window: today through (days_ahead) in the future.
        limit_date = now_utc + timedelta(days=days_ahead)

        # Ensure generation stops at medication end date (don't generate past it).
        if medication.end_datetime:
            limit_date = min(limit_date, medication.end_datetime)

        # CRITICAL: Fetch all existing reminders to prevent duplicates.
        # This avoids N+1 queries and ensures consistent duplicate detection.
        existing_stmt = select(Reminder.scheduled_time).where(
            and_(
                Reminder.medication_id == medication.id,
                Reminder.scheduled_time >= start_point,
                Reminder.scheduled_time <= limit_date
            )
        )
        existing_result = await session.execute(existing_stmt)

        # Build a set for O(1) lookup performance.
        # Normalize microseconds to 0 for exact matching.
        existing_reminders = {
            dt.replace(microsecond=0) for dt in existing_result.scalars().all()
        }

        reminders: list[Reminder] = []

        # Route to appropriate generation method based on frequency type.
        if medication.frequency_type in {
            FrequencyType.ONCE_DAILY, FrequencyType.TWICE_DAILY,
            FrequencyType.THREE_TIMES_DAILY, FrequencyType.FOUR_TIMES_DAILY,
            FrequencyType.CUSTOM
        }:
            scheduled_times: list[time] = []

            # Prefer user-defined reminder_times over defaults.
            # If user set custom times (e.g., ["08:30", "20:45"]), use those.
            if medication.reminder_times:
                for t in medication.reminder_times:
                    # Invalid time formats cause reminders to be skipped.
                    # Ensure reminder_times are ISO format strings ("HH:MM:SS") or time objects.
                    if isinstance(t, str):
                        try:
                            scheduled_times.append(time.fromisoformat(t))
                        except ValueError:
                            logger.warning("⚠️ Invalid time format in reminder_times: %s for medication %s", t, medication.id)
                            continue
                    elif isinstance(t, time):
                        scheduled_times.append(t)
            else:
                # Use default times if user didn't specify custom times.
                times_map = {
                    FrequencyType.ONCE_DAILY: [time(8, 0)],
                    FrequencyType.TWICE_DAILY: [time(8, 0), time(20, 0)],
                    FrequencyType.THREE_TIMES_DAILY: [time(8, 0), time(14, 0), time(20, 0)],
                    FrequencyType.FOUR_TIMES_DAILY: [time(6, 0), time(12, 0), time(18, 0), time(22, 0)],
                }
                scheduled_times = times_map.get(medication.frequency_type, [time(8, 0)])

            reminders = ReminderGenerator._generate_daily_reminders(
                medication, start_point, limit_date, scheduled_times, existing_reminders
            )

        elif medication.frequency_type == FrequencyType.EVERY_X_HOURS:
            # Handle interval-based dosing (e.g., "every 6 hours").
            # frequency_value contains the number of hours.
            reminders = ReminderGenerator._generate_interval_reminders(
                medication, start_point, limit_date, existing_reminders
            )

        # Log results for monitoring and troubleshooting.
        # If count is 0, check medication activation status and date boundaries.
        if reminders:
            logger.info(
                "✨ Generated %d reminders for %s (From %s to %s)",
                len(reminders),
                medication.name,
                start_point.date(),
                limit_date.date(),
            )
        else:
            logger.debug("No new reminders to generate for %s", medication.name)

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
        Generate reminders for fixed daily schedules (e.g., 8 AM, 2 PM, 8 PM).
        Handles timezone conversion and DST automatically.

        Args:
            medication: Medication record with timezone and schedule info
            start_utc: Start of generation window (UTC)
            end_utc: End of generation window (UTC)
            dose_times: List of times to generate reminders for each day
            existing_reminders: Set of existing reminder timestamps for duplicate prevention

        Returns:
            List of Reminder objects for this medication's daily schedule

        Troubleshooting:
            - Invalid timezone: Falls back to UTC with warning log
            - Reminders at wrong times: Check medication.timezone and dose_times
            - Reminders outside window: Verify start_datetime and end_datetime boundaries
            - Duplicate reminders: Ensure timestamp microsecond normalization (microsecond=0)
        """
        reminders: list[Reminder] = []

        # Get the medication's timezone for proper local time handling.
        try:
            tz = ZoneInfo(medication.timezone)
        except Exception:
            logger.warning("⚠️ Invalid timezone '%s' for medication %s, defaulting to UTC.", medication.timezone, medication.id)
            tz = dt_timezone.utc

        # Convert UTC date range to medication's local timezone.
        current_date = start_utc.astimezone(tz).date()
        end_date = end_utc.astimezone(tz).date()

        # Iterate through each day in the range.
        while current_date <= end_date:
            # Generate reminder for each dose time on this day.
            for dose_time in dose_times:
                # Combine local date with dose time in medication's timezone.
                local_dt = datetime.combine(current_date, dose_time, tzinfo=tz)

                # Convert back to UTC for consistent database storage.
                # Strip microseconds to match existing_reminders set (critical for duplicate checking).
                scheduled_utc = local_dt.astimezone(dt_timezone.utc).replace(microsecond=0)

                # Boundary checking for time window.
                if scheduled_utc < start_utc:
                    continue
                if scheduled_utc > end_utc:
                    continue

                # Skip if reminder already exists (prevents duplicates).
                if scheduled_utc in existing_reminders:
                    continue

                # Create and add reminder to batch.
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
        """
        Generate reminders for interval-based dosing (e.g., "every 6 hours").
        Calculates intervals from medication start time to end time.

        Args:
            medication: Medication record with frequency_value (hours between doses)
            start_utc: Start of generation window (UTC)
            end_utc: End of generation window (UTC)
            existing_reminders: Set of existing reminder timestamps for duplicate prevention

        Returns:
            List of Reminder objects for this medication's interval schedule

        Troubleshooting:
            - No reminders generated: Check frequency_value is set (number of hours)
            - Wrong interval timing: Verify medication.start_datetime (baseline for interval calc)
            - Too many/few reminders: Confirm frequency_value matches intended interval
            - First reminder too late: Check medication.start_datetime relative to generation window
        """
        # If no frequency value, nothing to generate.
        if not medication.frequency_value:
            return []

        reminders: list[Reminder] = []
        # Convert hours to timedelta for interval calculation.
        interval = timedelta(hours=medication.frequency_value)

        # Start from medication's initial start time.
        current = medication.start_datetime.replace(microsecond=0)

        # Align to first interval within generation window.
        if current < start_utc:
            # Calculate how many intervals have passed since medication start.
            delta = start_utc - current
            steps = int(delta.total_seconds() // interval.total_seconds())
            current += interval * steps
            # If rounding down, move to next interval.
            if current < start_utc:
                current += interval

        # Generate reminders at each interval within the time window.
        while current <= end_utc:
            # Skip if reminder already exists.
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
        """
        Batch generate reminders for all active medications.
        Uses database streaming to avoid OOM errors on large datasets.

        Args:
            session: Async database session
            days_ahead: Number of days to generate reminders for (default 7)

        Returns:
            Total number of reminders created across all medications

        Troubleshooting:
            - Generation stalls: Check database connectivity, verify active medication count
            - Out-of-memory errors: Increase yield_per value or reduce days_ahead
            - Commit fails: Check for duplicate key violations on reminder table
            - No reminders created: Verify active medications exist and frequency settings are valid
            - Check medication count: SELECT COUNT(*) FROM medications WHERE is_active=true;
        """
        # Fetch all active medications in chunks (not all at once).
        # yield_per(100) tells PostgreSQL to send rows in batches of 100.
        stmt = select(Medication).where(Medication.is_active.is_(True)).execution_options(yield_per=100)

        # Use async streaming to process medications one-by-one.
        result = await session.stream(stmt)

        total_created = 0

        # Process each medication and generate its reminders.
        async for med_row in result:
            med = med_row[0]

            # Generate reminders for this single medication.
            new_reminders = await ReminderGenerator.generate_reminders_for_medication(
                session, med, days_ahead
            )

            # Queue reminders for batch insert (not committed yet).
            # Batch inserts are much faster than individual inserts.
            if new_reminders:
                session.add_all(new_reminders)
                total_created += len(new_reminders)

        # Commit all reminders at once.
        if total_created > 0:
            await session.commit()
            logger.info("✅ Created %d new reminders.", total_created)

        return total_created