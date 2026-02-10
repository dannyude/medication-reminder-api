import logging
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from api.src.medications.models import Medication
from api.src.reminders.models import Reminder, ReminderStatus
from api.src.reminders.reminder_generator import ReminderGenerator

logger = logging.getLogger(__name__)


# CREATE & GENERATE REMINDERS
async def generate_and_save_reminders(
    session: AsyncSession,
    medication: Medication,
    days_ahead: int,
    clear_future: bool = False
) -> list[Reminder]:
    """
    Generate and save reminders for a medication with smart deduplication.

    This is the main entry point for reminder creation. It handles:
    1. Optional cleanup of existing future reminders (for medication updates)
    2. Generation of new reminder dates using ReminderGenerator
    3. Duplicate checking to prevent creating reminders that already exist
    4. Database persistence with proper transaction handling

    Args:
        session: Async database session
        medication: The medication to generate reminders for
        days_ahead: How many days into the future to generate reminders (e.g., 30)
        clear_future: If True, deletes all PENDING reminders after today before regenerating
                      (Used when medication schedule is updated)

    Returns:
        List of newly created Reminder objects (may be empty if all were duplicates)

    Example:
        # Generate 30 days of reminders for a new medication
        new_reminders = await generate_and_save_reminders(
            session=session,
            medication=med,
            days_ahead=30,
            clear_future=False
        )

        # Regenerate after user changes medication schedule
        updated_reminders = await generate_and_save_reminders(
            session=session,
            medication=med,
            days_ahead=30,
            clear_future=True  # Wipe old schedule, create new one
        )
    """

    # Optional Cleanup: If clear_future=True, delete all PENDING reminders for this medication that are scheduled in the future.

    # If clear_future=True, remove all PENDING reminders scheduled for the future.
    # This is used when a user updates a medication's schedule (e.g., changes time from 8am to 6am).
    # We only delete PENDING ones, not TAKEN/SKIPPED/MISSED (historical data).
    if clear_future:
        now_utc = datetime.now(timezone.utc)
        delete_stmt = (
            delete(Reminder)
            .where(
                and_(
                    Reminder.medication_id == medication.id,
                    Reminder.status == ReminderStatus.PENDING,
                    Reminder.scheduled_time > now_utc  # Only delete future reminders, keep past ones
                )
            )
        )
        await session.execute(delete_stmt)
        logger.info("🧹 Cleared future reminders for %s before regenerating.", medication.name)

    # GENERATE NEW REMINDERS

    # Use ReminderGenerator to calculate all reminder times based on frequency.
    # This respects the medication's start/end dates and timezone.
    potential_reminders = await ReminderGenerator.generate_reminders_for_medication(
        session, medication, days_ahead
    )

    # If no reminders were generated (e.g., medication already ended), commit cleanup and exit
    if not potential_reminders:
        if clear_future:
            await session.commit()
        return []

    # DUPLICATE CHECKING

    # Before saving, check for existing reminders in this time window.
    # This prevents creating duplicates if:
    # - A user accidentally calls the generate endpoint twice
    # - Reminders already exist from a previous generation
    # - There's overlap when regenerating (clear_future=False)

    start_date = potential_reminders[0].scheduled_time
    end_date = potential_reminders[-1].scheduled_time

    # Query database for any reminders in this time window
    existing_query = select(Reminder).where(
        and_(
            Reminder.medication_id == medication.id,
            Reminder.scheduled_time >= start_date,
            Reminder.scheduled_time <= end_date
        )
    )
    result = await session.execute(existing_query)
    # Convert to set for O(1) lookup time (much faster than list checking)
    existing_timestamps = {r.scheduled_time for r in result.scalars().all()}

    # Filter out any generated reminders that already exist
    # Only keep reminders with unique timestamps
    new_reminders = [
        r for r in potential_reminders
        if r.scheduled_time not in existing_timestamps
    ]

    # SAVE TO DATABASE
    # Add all new reminders to the session and commit in one transaction
    if new_reminders:
        session.add_all(new_reminders)

    await session.commit()
    logger.info("✅ Generated %d new reminders for %s", len(new_reminders), medication.name)

    return new_reminders

# READ REMINDERS

async def get_user_reminders(
    session: AsyncSession,
    user_id: UUID,
    status_filter: ReminderStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50
) -> tuple[Sequence[Reminder], int]:
    """
    Get all reminders for a user with optional filtering and pagination.

    This is the main query function for displaying reminders to a user.
    It supports filtering by status (PENDING, TAKEN, SKIPPED, MISSED) and date range.
    Results are paginated and sorted by scheduled time.

    Args:
        session: Async database session
        user_id: User to fetch reminders for
        status_filter: Optional filter by reminder status
        start_date: Optional start date (show reminders >= this time)
        end_date: Optional end date (show reminders <= this time)
        page: Page number (1-indexed) for pagination
        page_size: Number of results per page

    Returns:
        Tuple of (list of Reminder objects, total count) for pagination
    """

    # 1. Base Query - Start with all reminders for this user
    # Eager load medication data to avoid N+1 queries
    query = (
        select(Reminder)
        .where(Reminder.user_id == user_id)
    )

    # 2. Apply Filters - Allow filtering by status and/or date range
    if status_filter:
        query = query.where(Reminder.status == status_filter)
    if start_date:
        query = query.where(Reminder.scheduled_time >= start_date)
    if end_date:
        query = query.where(Reminder.scheduled_time <= end_date)

    # 3. Count Total - Get total matching records for pagination info
    # Using a subquery ensures the count respects all filters applied above
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 4. Pagination & Ordering - Apply sorting and limits for the final result
    # Order by scheduled_time (ascending) so users see reminders chronologically
    query = (
        query
        .options(joinedload(Reminder.medication))  # Eager load medication to prevent N+1
        .order_by(Reminder.scheduled_time.asc(), Reminder.id.asc())  # Secondary sort by ID for consistency
        .offset((page - 1) * page_size)  # Skip to the correct page
        .limit(page_size)  # Limit to page size
    )

    result = await session.execute(query)
    return result.scalars().unique().all(), total


async def get_medication_reminders(
    session: AsyncSession,
    medication_id: UUID,
    user_id: UUID,
    status_filter: ReminderStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50
) -> tuple[Sequence[Reminder], int]:
    """
    Get all reminders for a specific medication (scoped to user).

    This function retrieves reminders for a particular medication while
    ensuring the user owns that medication (security check).
    Supports same filtering and pagination as get_user_reminders.

    Args:
        session: Async database session
        medication_id: Medication to fetch reminders for
        user_id: User who owns the medication (security check)
        status_filter: Optional filter by reminder status
        start_date: Optional start date (show reminders >= this time)
        end_date: Optional end date (show reminders <= this time)
        page: Page number (1-indexed) for pagination
        page_size: Number of results per page

    Returns:
        Tuple of (list of Reminder objects, total count) for pagination
    """

    # 1. Base Query - Filter by both medication AND user
    # The user_id check ensures users can only see their own reminders
    query = (
        select(Reminder)
        .where(
            and_(
                Reminder.medication_id == medication_id,
                Reminder.user_id == user_id
            )
        )
    )

    # 2. Apply Filters
    if status_filter:
        query = query.where(Reminder.status == status_filter)
    if start_date:
        query = query.where(Reminder.scheduled_time >= start_date)
    if end_date:
        query = query.where(Reminder.scheduled_time <= end_date)

    # 3. Count Total (Efficient Subquery)
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 4. Pagination & Ordering
    query = (
        query
        .options(joinedload(Reminder.medication))
        .order_by(Reminder.scheduled_time.asc(), Reminder.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await session.execute(query)
    return result.scalars().unique().all(), total


# FETCH SINGLE REMINDER
async def get_reminder(
    session: AsyncSession,
    reminder_id: UUID,
    user_id: UUID
) -> Reminder:
    """
    Fetch a single reminder by ID (scoped to user for security).

    Internal helper function used by status update endpoints and the single reminder GET route.
    Validates that the reminder belongs to the requesting user.

    Args:
        session: Async database session
        reminder_id: ID of the reminder to fetch
        user_id: User ID to verify ownership

    Returns:
        The Reminder object with eager-loaded medication data

    Raises:
        HTTPException 404: If reminder not found or doesn't belong to user

    Example:
        reminder = await get_reminder(session, reminder_id, user_id)
        # Returns Reminder with medication already loaded, or raises 404
    """
    # Query for the reminder AND verify user ownership in the same query
    stmt = (
        select(Reminder)
        .options(joinedload(Reminder.medication))  # Eager load medication
        .where(
            and_(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id  # Security: verify ownership
            )
        )
    )
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    # If not found or doesn't belong to user, return 404
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    return reminder


# UPDATE REMINDER STATUS
async def mark_reminder_as_taken(
    session: AsyncSession,
    reminder_id: UUID,
    user_id: UUID,
    taken_at: datetime | None,
    notes: str | None
) -> Reminder:
    """
    Mark a reminder as TAKEN and decrement medication stock.

    When a user marks a reminder as taken, this function:
    1. Fetches the reminder (with ownership verification)
    2. Updates status to TAKEN with timestamp and notes
    3. Automatically decrements the medication's stock count
    4. Idempotent: calling twice returns the same reminder without issues

    Args:
        session: Async database session
        reminder_id: ID of reminder to mark taken
        user_id: User ID (ownership verification)
        taken_at: Optional timestamp when taken (defaults to now)
        notes: Optional notes (e.g., "took with water")

    Returns:
        Updated Reminder object

    Example:
        reminder = await mark_reminder_as_taken(
            session=session,
            reminder_id=reminder_id,
            user_id=user_id,
            taken_at=None,  # Will use current time
            notes="Took with breakfast"
        )
    """

    # 1. Fetch the reminder (verifies user ownership)
    reminder = await get_reminder(session, reminder_id, user_id)

    # 2. Idempotent: if already taken, just return it
    # Prevents errors if called multiple times
    if reminder.status == ReminderStatus.TAKEN:
        return reminder

    # 3. Update reminder status and metadata
    reminder.status = ReminderStatus.TAKEN
    reminder.notes = notes
    reminder.taken_at = taken_at or datetime.now(timezone.utc)
    reminder.updated_at = datetime.now(timezone.utc)

    # 4. Inventory Management - Decrement stock when medication is taken
    # This keeps track of how much medication is left
    if reminder.medication and reminder.medication.current_stock > 0:
        reminder.medication.current_stock -= 1
        logger.info("📉 Stock reduced for %s (now: %d)", reminder.medication.name, reminder.medication.current_stock)

    # 5. Persist changes to database
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def mark_reminder_as_skipped(
    session: AsyncSession,
    reminder_id: UUID,
    user_id: UUID,
    notes: str | None
) -> Reminder:
    """
    Mark a reminder as SKIPPED (user intentionally skipped this dose).

    Marks the reminder as skipped with optional notes.
    Does NOT affect medication stock.

    Args:
        session: Async database session
        reminder_id: ID of reminder to mark skipped
        user_id: User ID (ownership verification)
        notes: Optional reason for skipping (e.g., "Forgot to bring medicine")

    Returns:
        Updated Reminder object

    Example:
        reminder = await mark_reminder_as_skipped(
            session=session,
            reminder_id=reminder_id,
            user_id=user_id,
            notes="Forgot to bring medicine to work"
        )
    """

    # 1. Fetch the reminder (verifies user ownership)
    reminder = await get_reminder(session, reminder_id, user_id)

    # 2. Update reminder status
    reminder.status = ReminderStatus.SKIPPED
    reminder.notes = notes  # Store reason for skipping
    reminder.updated_at = datetime.now(timezone.utc)

    # 3. Persist to database
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def mark_reminder_as_missed(
    session: AsyncSession,
    reminder_id: UUID,
    user_id: UUID,
    notes: str | None
) -> Reminder:
    """
    Mark a reminder as MISSED (user forgot or couldn't take medication).

    Records that a scheduled dose was missed, with optional notes.
    Does NOT affect medication stock.
    Useful for tracking medication adherence history.

    Args:
        session: Async database session
        reminder_id: ID of reminder to mark missed
        user_id: User ID (ownership verification)
        notes: Optional reason for missing (e.g., "Was out of town")

    Returns:
        Updated Reminder object

    Example:
        reminder = await mark_reminder_as_missed(
            session=session,
            reminder_id=reminder_id,
            user_id=user_id,
            notes="Was out of town without medication"
        )
    """

    # 1. Fetch the reminder (verifies user ownership)
    reminder = await get_reminder(session, reminder_id, user_id)

    # 2. Update reminder status
    reminder.status = ReminderStatus.MISSED
    reminder.notes = notes  # Store reason for missing
    reminder.updated_at = datetime.now(timezone.utc)

    # 3. Persist to database
    await session.commit()
    await session.refresh(reminder)
    return reminder


# DELETE REMINDER
async def delete_reminder(
    session: AsyncSession,
    reminder_id: UUID,
    user_id: UUID
) -> None:
    """
    Delete a reminder from the database.

    Permanently removes a reminder. Note: This does NOT restore medication stock
    if the reminder was marked as taken. Use with caution.

    Args:
        session: Async database session
        reminder_id: ID of reminder to delete
        user_id: User ID (ownership verification)

    Returns:
        None

    Example:
        await delete_reminder(
            session=session,
            reminder_id=reminder_id,
            user_id=user_id
        )
        # Reminder is permanently deleted
    """

    # 1. Fetch reminder (verifies user ownership and existence)
    reminder = await get_reminder(session, reminder_id, user_id)

    # 2. Delete from database
    await session.delete(reminder)
    await session.commit()

    logger.info("🗑️ Reminder %s deleted for user %s", reminder_id, user_id)
