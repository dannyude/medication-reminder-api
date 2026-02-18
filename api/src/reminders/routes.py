import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession


from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.reminders.models import ReminderStatus
from api.src.users.models import User
from api.src.reminders import crud
from api.src.reminders.schemas import (
    ReminderResponse,
    ReminderListResponse,
    MarkAsMissedSchema,
    MarkAsSkippedSchema,
    MarkAsTakenSchema,
)

from api.src.medications import crud as med_crud

router = APIRouter(prefix="/reminders", tags=["Reminders"])
logger = logging.getLogger(__name__)

# Create Reminders
@router.post("/medications/{medication_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_medication_reminders(
    medication_id: UUID,
    days_ahead: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate reminders for a specific medication.
    Checks for duplicates before saving.
    """
    # 1. Ensure User owns the medication
    medication = await med_crud.get_medication(
        session, medication_id, current_user.id
    )

    # 2. Generate Safely (CRUD handles duplicate checks)
    new_reminders = await crud.generate_and_save_reminders(
        session=session,
        medication=medication,
        days_ahead=days_ahead
    )

    return {
        "message": f"Generated {len(new_reminders)} new reminders for {medication.name}",
        "count": len(new_reminders),
        "medication": medication.name,
        "days_ahead": days_ahead
    }


# LIST (Read History / Today / Upcoming)
@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    status_filter: Optional[ReminderStatus] = Query(
        None,
        description="Filter by reminder status (PENDING, TAKEN, SKIPPED, MISSED)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Show reminders scheduled after this time (UTC)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Show reminders scheduled before this time (UTC)"
    ),
    # 📄 Pagination Parameters
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    # Dependencies
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all reminders for the current user.
    - For 'Today': set start_date=Today 00:00 & end_date=Today 23:59
    - For 'History': set end_date=Now
    """
    reminders, total = await crud.get_user_reminders(
        session=session,
        user_id=current_user.id,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    return {
        "total": total,
        "reminders": reminders,
        "page": page,
        "page_size": page_size
    }


# LIST REMINDERS FOR A SPECIFIC MEDICATION
@router.get("/medications/{medication_id}", response_model=ReminderListResponse)
async def get_medication_reminders_route(
    medication_id: UUID,
    status_filter: Optional[ReminderStatus] = Query(
        None,
        description="Filter by reminder status (PENDING, TAKEN, SKIPPED, MISSED)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Show reminders scheduled after this time (UTC)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Show reminders scheduled before this time (UTC)"
    ),
    # 📄 Pagination Parameters
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    # Dependencies
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all reminders for a specific medication.
    Filters by both medication and user for security.
    """
    reminders, total = await crud.get_medication_reminders(
        session=session,
        medication_id=medication_id,
        user_id=current_user.id,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    return {
        "total": total,
        "reminders": reminders,
        "page": page,
        "page_size": page_size
    }


# GET SINGLE REMINDER
@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_single_reminder(
    reminder_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get details of a specific reminder."""
    return await crud.get_reminder(session, reminder_id, current_user.id)


# ACTION: TAKE
@router.post("/{reminder_id}/taken", response_model=ReminderResponse)
async def mark_reminder_taken(
    reminder_id: UUID,
    payload: MarkAsTakenSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Mark as TAKEN. Decrements inventory stock."""
    reminder = await crud.mark_reminder_as_taken(
        session=session,
        reminder_id=reminder_id,
        user_id=current_user.id,
        taken_at=payload.taken_at,
        notes=payload.notes
    )
    return reminder


# ACTION: SKIP
@router.post("/{reminder_id}/skipped", response_model=ReminderResponse)
async def mark_reminder_skipped(
    reminder_id: UUID,
    payload: MarkAsSkippedSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Mark as SKIPPED. Does NOT affect inventory."""
    reminder = await crud.mark_reminder_as_skipped(
        session=session,
        reminder_id=reminder_id,
        user_id=current_user.id,
        notes=payload.notes # Assuming schema has 'notes' (or reason)
    )
    return reminder


# ACTION: MISS
@router.post("/{reminder_id}/missed", response_model=ReminderResponse)
async def mark_reminder_missed(
    reminder_id: UUID,
    payload: MarkAsMissedSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Mark as MISSED. Does NOT affect inventory."""
    reminder = await crud.mark_reminder_as_missed(
        session=session,
        reminder_id=reminder_id,
        user_id=current_user.id,
        notes=payload.notes
    )
    return reminder


# DELETE
@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a reminder. Does not restore inventory."""
    await crud.delete_reminder(
        session=session,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
