import logging
from datetime import datetime
from typing import Optional, Sequence
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.users.models import User
from api.src.reminders import crud
from api.src.reminders.schemas import (
    ReminderResponse,
    ReminderListResponse,
    ReminderStatus,
    MarkReminderSchema
)
from api.src.reminders.reminder_generator import ReminderGenerator
from api.src.medications import crud as med_crud

router = APIRouter(prefix="/reminders", tags=["Reminders"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=ReminderListResponse)
async def list_reminders(
    status_filter: Optional[ReminderStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all reminders for current user (paginated)."""

    # 1. Fetch Data (1 Query only!)
    reminders, total = await crud.get_user_reminders(
        session, str(current_user.id), status_filter,
        start_date, end_date, page, page_size
    )

    # 2. Map Responses in memory (Fast)
    responses = [ReminderResponse.model_validate(r) for r in reminders]

    return ReminderListResponse(
        total=total,
        reminders=responses,
        page=page,
        page_size=page_size
    )


@router.get("/today", response_model=list[ReminderResponse])
async def get_todays_reminders(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all reminders for today."""
    reminders = await crud.get_todays_reminders(session, str(current_user.id))
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.get("/upcoming", response_model=list[ReminderResponse])
async def get_upcoming_reminders(
    hours_ahead: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get upcoming reminders for the next X hours."""
    reminders = await crud.get_upcoming_reminders(
        session, str(current_user.id), hours_ahead
    )
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.patch("/{reminder_id}", response_model=ReminderResponse)
async def mark_reminder(
    reminder_id: str,
    mark_data: MarkReminderSchema,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark reminder as taken/missed/skipped and update stock."""

    reminder = await crud.mark_reminder(
        session, reminder_id, str(current_user.id), mark_data
    )

    return ReminderResponse.model_validate(reminder)


@router.post("/medications/{medication_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_medication_reminders(
    medication_id: UUID,
    days_ahead: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate reminders for a specific medication."""

    medication = await med_crud.get_medication(
        session, medication_id, current_user.id
    )

    reminders = await ReminderGenerator.generate_reminders_for_medication(
        session, medication, days_ahead
    )

    if reminders:
        session.add_all(reminders)
        await session.commit()

    return {
        "message": f"Generated {len(reminders)} reminders for {medication.name}",
        "count": len(reminders),
        "medication": medication.name,
        "days_ahead": days_ahead
    }