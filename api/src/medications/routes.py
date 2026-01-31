import logging
from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.reminders.reminder_generator import ReminderGenerator
from api.src.users.models import User
from api.src.medications import crud
from api.src.medications.schemas import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationStockUpdate,
    MedicationPaginationResponse
)
from api.src.reminders.crud import generate_and_save_reminders

router = APIRouter(prefix="/medications", tags=["Medications"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    medication_in: MedicationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new medication."""
    medication = await crud.create_medication(
        session,
        current_user.id,
        medication_in
    )

    new_reminders = await ReminderGenerator.generate_reminders_for_medication(
        session = session,
        medication = medication
    )

    if new_reminders:
        session.add_all(new_reminders)
        await session.commit()


    return medication


@router.get("/get_all", response_model=MedicationPaginationResponse)
async def get_medications(
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all medications for current user with pagination."""
    meds, total_count = await crud.get_user_medications(
        session, current_user.id, active_only, page, page_size
    )

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "medications": meds
    }


@router.get("/get_specific/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific medication."""
    medication = await crud.get_medication(
        session,
        medication_id,
        current_user.id
    )

    return medication

@router.patch("/{medication_id}", response_model=MedicationResponse) # 1. Removed redundant "/update"
async def update_medication(
    medication_id: UUID,
    medication_update: MedicationUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a medication and regenerate schedule if needed."""

    # 1. Perform the Update
    updated_medication = await crud.update_medication(
        session,
        medication_id,
        current_user.id,
        medication_update
    )

    # 2. Check for Schedule Changes 🕵️‍♂️
    # We convert the update model to a dict (excluding unset/null values)
    # to see exactly what the user sent us.
    update_data = medication_update.model_dump(exclude_unset=True)

    # Define which fields alter the schedule
    schedule_impacting_fields = {
        "frequency_type",
        "frequency_value",
        "reminder_times",  # <--- CRITICAL: Don't forget this!
        "start_date",      # <--- Note: start_date, not start_datetime
        "start_time",
        "end_date",
        "end_time",
        "timezone"
    }

    # If any of the sent fields are in our "Impact List", regenerate.
    schedule_changed = any(field in update_data for field in schedule_impacting_fields)

    if schedule_changed:
        # 3. Use the Smart Function (Clean + Generate + Deduplicate)
        # We don't need to manually clear/add/commit here. The CRUD does it.
        await generate_and_save_reminders(
            session = session,
            medication = updated_medication,
            days_ahead = 30,          # Generate 30 days into the future
            clear_future = True       # Clear future reminders before regenerating
        )
    return updated_medication


@router.get("/low_stock", response_model=list[MedicationResponse])
async def get_low_stock_medications(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get medications that are low in stock for current user."""
    medications = await crud.get_low_stock_medications(
        session,
        current_user.id
    )
    return medications

@router.patch("/{medication_id}/stock", response_model=MedicationResponse)
async def update_stock_endpoint(
    medication_id: UUID,
    stock_update: MedicationStockUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update medication stock.
    - **quantity**: Positive to add stock, negative to reduce
    - **note**: Optional note about the change
    """

    medication = await crud.update_medication_stock(
        session,
        medication_id,
        current_user.id,
        stock_update
    )

    return medication

@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    medication_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a medication."""
    await crud.delete_medication(
        session,
        medication_id,
        current_user.id
    )