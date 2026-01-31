import logging
from typing import Sequence
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.src.medications.models import Medication
from api.src.logs.models import MedicationLog

from api.src.medications.schemas import MedicationCreate, MedicationUpdate, MedicationStockUpdate
from api.src.medications.utils import combine_datetime_with_timezone

logger = logging.getLogger(__name__)

"""CRUD operations for Medications."""


def _merge_start_datetime_fields(
    medication: Medication,
    update_data: dict
) -> None:
    """
    Helper function to merge start_date, start_time, and timezone updates.
    Modifies the medication object in place and removes consumed keys from update_data.
    """
    current_tz = medication.timezone
    current_local = medication.start_datetime.astimezone(ZoneInfo(current_tz))
    # Merge update data with existing local values
    new_date = update_data.get("start_date", current_local.date())
    new_time = update_data.get("start_time", current_local.time())
    new_tz = update_data.get("timezone", current_tz)

    medication.start_datetime = combine_datetime_with_timezone(new_date, new_time, new_tz)
    medication.timezone = new_tz

    # Remove consumed keys
    for key in ["start_date", "start_time", "timezone"]:
        update_data.pop(key, None)


def _merge_end_datetime_fields(
    medication: Medication,
    update_data: dict
) -> None:
    """
    Helper function to merge end_date and end_time updates.
    Modifies the medication object in place and removes consumed keys from update_data.
    """
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
            medication.end_datetime = combine_datetime_with_timezone(
                new_end_date, new_end_time, tz_to_use
            )

    # Case B: Updating ONLY the End TIME (must preserve existing date)
    elif "end_time" in update_data and medication.end_datetime:
        current_end_local = medication.end_datetime.astimezone(ZoneInfo(tz_to_use))
        medication.end_datetime = combine_datetime_with_timezone(
            current_end_local.date(),
            update_data["end_time"],
            tz_to_use
        )

    # Remove consumed keys
    update_data.pop("end_date", None)
    update_data.pop("end_time", None)


async def create_medication(
    session: AsyncSession,
    user_id: UUID,
    medication_in: MedicationCreate
) -> Medication:

    # 1. Extract and map fields from Pydantic model
    try:
        data = medication_in.model_dump(
            exclude={
                "start_date", "start_time",
                "end_date", "end_time",
                "start_datetime_utc", "end_datetime_utc"
            }
        )

        # 2. Explicitly map to your Database Column Names
        # logic MUST be inside the try block to be caught by the except block below
        data["start_datetime"] = medication_in.start_datetime_utc

        if medication_in.end_datetime_utc:
            data["end_datetime"] = medication_in.end_datetime_utc

    except AttributeError as e:
        logger.error("AttributeError during medication creation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: Missing required field: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error during medication creation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the medication data."
        ) from e

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

        logger.info("Created medication %s for user %s", medication.id, user_id)

        return medication

    except IntegrityError as e:
        # Catches DB constraints (e.g., if you have a unique constraint on medication names)
        await session.rollback()
        logger.warning("⚠️ Integrity Error (Duplicate?): %s", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A medication with this specific configuration might already exist."
        ) from e

    except SQLAlchemyError as e:
        # Catches general database failures (connection lost, bad SQL types)
        await session.rollback()
        logger.error("🔥 Database Error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while saving medication."
        ) from e

    except Exception as e:
        await session.rollback()
        logger.error("SQLAlchemy Error: %s", e)
        # This will help you see EXACTLY which key is failing in your logs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mapping Error: {str(e)}"
        ) from e

# Read all medications for a user
async def get_user_medications(
    session: AsyncSession,
    user_id: UUID,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50
) -> tuple[list[Medication], int]:
    """Get all medications for a user with pagination and eager loading."""

    try:
        # 1. Base Query
        query = select(Medication).where(Medication.user_id == user_id)

        if active_only:
            query = query.where(Medication.is_active.is_(True))

        # 2. Count Total (Robust method using subquery to respect filters)
        # This prevents counting *all* meds if we only filtered for *active* ones
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 3. Apply Pagination & Ordering
        # ALWAYS order by created_at desc so new meds show first
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(desc(Medication.created_at))
            .offset(offset)
            .limit(page_size)
            # 🚀 PERFORMANCE BOOST: Load reminders automatically
            # If your UI shows "Next reminder: 2pm", you NEED this line.
            .options(selectinload(Medication.reminders))
        )

        result = await session.execute(query)
        medications = result.scalars().all()

        return list(medications), total

    except SQLAlchemyError as e:
        logger.error("Database error while fetching medications: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching medications."
        ) from e

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
        _merge_start_datetime_fields(medication, update_data)

    # 2. Handle END Schedule Updates
    if any(k in update_data for k in ["end_date", "end_time"]):
        _merge_end_datetime_fields(medication, update_data)

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
        logger.exception("Update failed for medication %s", medication_id)
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
        logger.exception("Failed to update stock for medication %s", medication_id)
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
    stmt = select(MedicationLog).where(MedicationLog.medication_id == medication_id)
    result = await session.execute(stmt)
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
