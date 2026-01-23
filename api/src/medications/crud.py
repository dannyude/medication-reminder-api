import logging
from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import  datetime, timezone
from fastapi import HTTPException, status

from api.src.medications.models import Medication, Reminder, MedicationLog, ReminderStatus
from api.src.medications.schemas import MedicationCreate, MedicationUpdate

logger = logging.getLogger(__name__)


async def create_medication(
    session: AsyncSession,
    user_id: UUID,
    medication_in: MedicationCreate
) -> Medication:

    # Dump Api data to dict
    data = medication_in.model_dump(exclude_unset=True)

    # Remove unneeded fields (Split inputs & Pydantic computed keys)
    data.pop("start_date", None)
    data.pop("start_time", None)
    data.pop("end_date", None)
    data.pop("end_time", None)
    data.pop("start_datetime_utc", None)
    data.pop("end_datetime_utc", None)

    # 👇 CORRECT MAPPING: Use the DB Column Names ('start_date', 'end_date')
    data["start_date"] = medication_in.start_datetime_utc

    if medication_in.end_datetime_utc:
        data["end_date"] = medication_in.end_datetime_utc

    # Create medication instance
    # data now has keys: 'name', 'timezone', 'start_date', etc.
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
        logger.error(f"Failed to create medication for user {user_id}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error: {e}"
        ) from e

# Read all medications for a user
async def get_user_medications(
    session: AsyncSession,
    user_id: UUID,
    active_only: bool = True
) -> list[Medication]:
    """Get all medications for a user."""

    query = select(Medication).where(Medication.user_id == user_id)

    if active_only:
        query = query.where(Medication.is_active.is_(True))

    result = await session.execute(query.order_by(Medication.created_at.desc()))
    return list(result.scalars().all())

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

    for field, value in update_data.items():
        setattr(medication, field, value)

    medication.updated_at = datetime.now(timezone.utc)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()

        logger.exception("Failed to update medication %s for user %s", medication_id, user_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the medication"
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