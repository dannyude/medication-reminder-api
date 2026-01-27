import logging
from typing import Sequence
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.medications.models import Medication
from api.src.logs.models import MedicationLog

from api.src.medications.schemas import MedicationCreate, MedicationUpdate, MedicationStockUpdate
from api.src.medications.utils import combine_datetime_with_timezone

logger = logging.getLogger(__name__)

"""CRUD operations for Medications."""
async def create_medication(
    session: AsyncSession,
    user_id: UUID,
    medication_in: MedicationCreate
) -> Medication:

    # 1. Extract and map fields from Pydantic model
    data = medication_in.model_dump(
        exclude={
            "start_date", "start_time",
            "end_date", "end_time",
            "start_datetime_utc", "end_datetime_utc"
        }
    )

    # 2. Explicitly map to your Database Column Names
    data["start_datetime"] = medication_in.start_datetime_utc

    if medication_in.end_datetime_utc:
        data["end_datetime"] = medication_in.end_datetime_utc

    # 3. Create the instance
    # This ensures NO extra keys like 'start_date' reach SQLAlchemy
    medication = Medication(
        user_id=user_id,
        **data
    )

    session.add(medication)

    try:
        await session.commit()
        await session.refresh(medication)

        return medication


    except Exception as e:
        await session.rollback()
        logger.error(f"SQLAlchemy Error: {e}")
        # This will help you see EXACTLY which key is failing in your logs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mapping Error: {str(e)}"
        )

# Read all medications for a user
async def get_user_medications(
    session: AsyncSession,
    user_id: UUID,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50
) -> tuple[list[Medication], int]:
    """Get all medications for a user."""

    query = select(Medication).where(Medication.user_id == user_id)

    if active_only:
        query = query.where(Medication.is_active.is_(True))

    # instead of func.count()
    count_query = select(func.count(Medication.id)).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    medications = result.scalars().all()

    return list(medications), total

# Read a specific medication
async def get_medication(
    session: AsyncSession,
    medication_id: UUID,
    user_id: UUID,
) -> Medication:
    """Get a specific medication."""

    stmt = select(Medication).where(
        and_(
            Medication.id == medication_id,
            Medication.user_id == user_id
        )
    )
    result = await session.execute(stmt)
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )

    return medication

# Update medication
async def update_medication(
    session: AsyncSession,
    medication_id: UUID,
    user_id: UUID,
    medication_update: MedicationUpdate
) -> Medication:
    """Update a medication."""

    medication = await get_medication(session, medication_id, user_id)
    update_data = medication_update.model_dump(exclude_unset=True)

    # 1. Handle START Schedule Updates
    if any(k in update_data for k in ["start_date", "start_time", "timezone"]):
        # Resolve current local time to preserve missing fields (date vs time)
        current_tz = medication.timezone
        current_local = medication.start_datetime.astimezone(ZoneInfo(current_tz))

        # Merge update data with existing local values
        new_date = update_data.get("start_date", current_local.date())
        new_time = update_data.get("start_time", current_local.time())
        new_tz = update_data.get("timezone", current_tz)

        medication.start_datetime = combine_datetime_with_timezone(new_date, new_time, new_tz)
        medication.timezone = new_tz

        # Consume keys to prevent generic overwrite
        for k in ["start_date", "start_time", "timezone"]:
            update_data.pop(k, None)

    # 2. Handle END Schedule Updates
    if any(k in update_data for k in ["end_date", "end_time"]):
        tz_to_use = medication.timezone

        # Case A: Updating the End DATE (and optionally time)
        if "end_date" in update_data:
            new_end_date = update_data["end_date"]

            if new_end_date is None:
                medication.end_datetime = None
            else:
                # Default to end-of-day OR preserve existing time
                existing_time = time(23, 59, 59)
                if medication.end_datetime:
                    existing_time = medication.end_datetime.astimezone(ZoneInfo(tz_to_use)).time()

                new_end_time = update_data.get("end_time", existing_time)
                medication.end_datetime = combine_datetime_with_timezone(new_end_date, new_end_time, tz_to_use)

        # Case B: Updating ONLY the End TIME (must preserve existing date)
        elif "end_time" in update_data and medication.end_datetime:
            current_end_local = medication.end_datetime.astimezone(ZoneInfo(tz_to_use))
            medication.end_datetime = combine_datetime_with_timezone(
                current_end_local.date(),
                update_data["end_time"],
                tz_to_use
            )

        update_data.pop("end_date", None)
        update_data.pop("end_time", None)

    # 3. Validation: Prevent Negative Schedules
    if medication.end_datetime is not None:
        if medication.end_datetime <= medication.start_datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date/time must be after start date/time"
            )

    # 4. Generic Field Update
    for field, value in update_data.items():
        setattr(medication, field, value)

    medication.updated_at = datetime.now(timezone.utc)

    try:
        await session.commit()
        await session.refresh(medication)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Update failed for medication {medication_id}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Update failed") from e

    return medication


async def get_low_stock_medications(
    session: AsyncSession,
    user_id: UUID
) -> Sequence[Medication]:
    """Get medications that are low in stock for a user."""

    stmt = select(Medication).where(
        and_(
            Medication.user_id == user_id,
            Medication.current_stock <= Medication.low_stock_threshold,
            Medication.is_active.is_(True)
        )
    ).order_by(Medication.current_stock.asc())

    result = await session.execute(stmt)
    return result.scalars().all()

async def update_medication_stock(
    session: AsyncSession,
    medication_id: UUID,
    user_id: UUID,
    stock_update: MedicationStockUpdate
) -> Medication:
    """
    Update the current stock of a medication.
    Uses delta logic (+/-) to handle concurrent updates safely.
    """

    medication = await get_medication(session, medication_id, user_id)

    # Calculate new stock
    new_stock = medication.current_stock + stock_update.quantity

    # Validate
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reduce stock by {abs(stock_update.quantity)}. Current stock is {medication.current_stock}."
        )

    # Update State
    medication.current_stock = new_stock
    medication.updated_at = datetime.now(timezone.utc)

    try:
        await session.commit()
        await session.refresh(medication)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Failed to update stock for medication {medication_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update medication stock"
        ) from e

    return medication

# Delete medication
async def delete_medication(
    session: AsyncSession,
    medication_id: UUID,
    user_id: UUID
) -> None:
    """
    Hybrid delete:
    - Soft delete if medication has logs
    - Hard delete if no history exists
    """

    medication = await get_medication(session, medication_id, user_id)

    # Check for existing medication logs
    smt = select(MedicationLog).where(MedicationLog.medication_id == medication_id)
    result = await session.execute(smt)
    has_logs = result.scalars().first()

    try:
        if has_logs:
            # Soft delete
            medication.is_active = False
            medication.updated_at = datetime.now(timezone.utc)
            logger.info("Soft deleted medication %s for user %s", medication_id, user_id)
        else:
            logger.info("Hard deleting medication %s for user %s", medication_id, user_id)
            await session.delete(medication)
        await session.commit()
    except Exception as e:
        await session.rollback()

        logger.exception("Failed to delete medication %s for user %s", medication_id, user_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the medication"
        ) from e
