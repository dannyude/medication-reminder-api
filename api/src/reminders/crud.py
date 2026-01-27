import logging
from datetime import datetime, timedelta, timezone
from typing import Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload # <--- 1. CRITICAL IMPORT
from fastapi import HTTPException, status

from api.src.reminders.models import Reminder, ReminderStatus
from api.src.reminders.schemas import MarkReminderSchema

logger = logging.getLogger(__name__)

async def get_user_reminders(
    session: AsyncSession,
    user_id: str,
    status_filter: ReminderStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50
) -> tuple[Sequence[Reminder], int]:
    """Get paginated reminders for a user."""

    query = (
        select(Reminder)
        .options(joinedload(Reminder.medication))
        .where(Reminder.user_id == uuid.UUID(user_id))
    )

    if status_filter:
        query = query.where(Reminder.status == status_filter)

    if start_date:
        query = query.where(Reminder.scheduled_time >= start_date)

    if end_date:
        query = query.where(Reminder.scheduled_time <= end_date)


    count_stmt = select(func.count(Reminder.id)).select_from(query.subquery()) # type: ignore
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # 3. Add Join & Pagination for the real fetch
    query = (
        query
        .options(joinedload(Reminder.medication))
        .order_by(Reminder.scheduled_time.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await session.execute(query)

    reminders = result.scalars().unique().all()

    return reminders, total


async def get_upcoming_reminders(
    session: AsyncSession,
    user_id: str,
    hours_ahead: int = 24
) -> Sequence[Reminder]:
    """Get upcoming reminders for the next X hours."""

    now = datetime.now(timezone.utc)
    future = now + timedelta(hours=hours_ahead)

    stmt = (
        select(Reminder)
        .options(joinedload(Reminder.medication)) # <--- Load Meds
        .where(
            and_(
                Reminder.user_id == uuid.UUID(user_id),
                Reminder.status == ReminderStatus.PENDING,
                Reminder.scheduled_time >= now,
                Reminder.scheduled_time <= future
            )
        )
        .order_by(Reminder.scheduled_time.asc())
    )

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_reminder(
    session: AsyncSession,
    reminder_id: str,
    user_id: str
) -> Reminder:
    """Get a specific reminder."""

    try:
        reminder_uuid = uuid.UUID(reminder_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    stmt = (
        select(Reminder)
        .options(joinedload(Reminder.medication)) # <--- Load Meds
        .where(
            and_(
                Reminder.id == reminder_uuid,
                Reminder.user_id == user_uuid
            )
        )
    )
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    return reminder

async def mark_reminder(
    session: AsyncSession,
    reminder_id: str,
    user_id: str,
    mark_data: MarkReminderSchema
) -> Reminder:
    """Mark reminder as taken/missed/skipped."""

    reminder = await get_reminder(session, reminder_id, user_id)

    # Update status
    reminder.status = mark_data.status
    reminder.notes = mark_data.notes

    # Set taken_at
    if mark_data.status == ReminderStatus.TAKEN:
        # Set timestamp
        reminder.taken_at = mark_data.taken_at or datetime.now(timezone.utc)

        # 🟢 CRITICAL: Reduce Stock Here
        # Since we used 'joinedload' in get_reminder, reminder.medication is available.
        if reminder.medication and reminder.medication.current_stock > 0:
            reminder.medication.current_stock -= 1
            logger.info(f"Stock reduced for {reminder.medication.name}. New stock: {reminder.medication.current_stock}")

    reminder.updated_at = datetime.now(timezone.utc)

    # 4. Commit everything (Reminder update + Stock update) atomically
    await session.commit()
    await session.refresh(reminder)

    logger.info(f"Reminder {reminder_id} marked as {mark_data.status}")

    return reminder

async def get_todays_reminders(
    session: AsyncSession,
    user_id: str
) -> Sequence[Reminder]:
    """Get all reminders for today (UTC based)."""

    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    stmt = (
        select(Reminder)
        .options(joinedload(Reminder.medication))
        .where(
            and_(
                Reminder.user_id == uuid.UUID(user_id),
                Reminder.scheduled_time >= start_of_day,
                Reminder.scheduled_time < end_of_day
            )
        )
        .order_by(Reminder.scheduled_time.asc())
    )

    result = await session.execute(stmt)
    return result.scalars().unique().all()