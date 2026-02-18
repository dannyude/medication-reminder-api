import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.src.logs.models import MedicationLog
from api.src.logs.schemas import (
    MedicationLogCreate,
    MedicationLogUpdate,
    AdherenceStats,
    MedicationAdherenceReport,
    UserAdherenceReport,
)
from api.src.logs.enums import LogAction
from api.src.medications.models import Medication

logger = logging.getLogger(__name__)


async def create_medication_log(
    db: AsyncSession,
    log_data: MedicationLogCreate,
    user_id: UUID,
) -> MedicationLog:
    """
    Create a new medication log entry.

    Args:
        db: Database session
        log_data: Log creation data
        user_id: ID of the user creating the log

    Returns:
        The created medication log

    Raises:
        HTTPException: If medication doesn't exist or doesn't belong to user
    """
    try:
        # Fetch the medication to ensure it exists and belongs to the user
        medication_query = select(Medication).where(
            and_(
                Medication.id == log_data.medication_id,
                Medication.user_id == user_id,
            )
        )
        result = await db.execute(medication_query)
        medication = result.scalar_one_or_none()

        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found or does not belong to user"
            )

        # Create log with snapshot data
        log = MedicationLog(
            user_id=user_id,
            medication_id=log_data.medication_id,
            reminder_id=log_data.reminder_id,
            medication_name_snapshot=medication.name,
            dosage_snapshot=medication.dosage,
            action=log_data.action,
            source=log_data.source,
            taken_at=log_data.taken_at,
            dosage_taken=log_data.dosage_taken or medication.dosage,
            notes=log_data.notes,
            side_effects=log_data.side_effects,
        )

        db.add(log)
        await db.commit()
        await db.refresh(log)

        logger.info("Created medication log %s for user %s", log.id, user_id)
        return log

    except IntegrityError as e:
        await db.rollback()
        logger.error("Integrity error creating medication log: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        ) from e

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Database error creating medication log: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        ) from e


async def get_medication_log(
    db: AsyncSession,
    log_id: UUID,
    user_id: UUID,
) -> MedicationLog:
    """
    Get a specific medication log by ID.

    Args:
        db: Database session
        log_id: ID of the log to retrieve
        user_id: ID of the user (for authorization)

    Returns:
        The medication log

    Raises:
        HTTPException: If log not found or doesn't belong to user
    """
    query = select(MedicationLog).where(
        and_(
            MedicationLog.id == log_id,
            MedicationLog.user_id == user_id,
        )
    ).options(selectinload(MedicationLog.medication))

    result = await db.execute(query)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication log not found"
        )

    return log


async def get_user_medication_logs(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    medication_id: Optional[UUID] = None,
    action: Optional[LogAction] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_voided: bool = False,
) -> tuple[Sequence[MedicationLog], int]:
    """
    Get medication logs for a user with optional filtering.

    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        medication_id: Filter by specific medication
        action: Filter by action type
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        include_voided: Whether to include voided logs

    Returns:
        Tuple of (logs, total_count)
    """
    # Build base query
    conditions = [MedicationLog.user_id == user_id]

    if not include_voided:
        conditions.append(MedicationLog.is_voided == False)

    if medication_id:
        conditions.append(MedicationLog.medication_id == medication_id)

    if action:
        conditions.append(MedicationLog.action == action)

    if start_date:
        conditions.append(MedicationLog.taken_at >= start_date)

    if end_date:
        conditions.append(MedicationLog.taken_at <= end_date)

    # Query for logs
    query = (
        select(MedicationLog)
        .where(and_(*conditions))
        .order_by(desc(MedicationLog.taken_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    # Count total
    count_query = select(func.count()).select_from(MedicationLog).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return logs, total


async def update_medication_log(
    db: AsyncSession,
    log_id: UUID,
    user_id: UUID,
    update_data: MedicationLogUpdate,
) -> MedicationLog:
    """
    Update a medication log (limited fields only).

    Args:
        db: Database session
        log_id: ID of the log to update
        user_id: ID of the user (for authorization)
        update_data: Fields to update

    Returns:
        The updated medication log

    Raises:
        HTTPException: If log not found, voided, or doesn't belong to user
    """
    log = await get_medication_log(db, log_id, user_id)

    if log.is_voided:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a voided log entry"
        )

    # Only allow updating certain fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        setattr(log, key, value)

    try:
        await db.commit()
        await db.refresh(log)
        logger.info("Updated medication log %s for user %s", log_id, user_id)
        return log
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Database error updating medication log: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        ) from e


async def void_medication_log(
    db: AsyncSession,
    log_id: UUID,
    user_id: UUID,
    void_reason: Optional[str] = None,
) -> MedicationLog:
    """
    Void a medication log (soft delete - mark as error).

    Args:
        db: Database session
        log_id: ID of the log to void
        user_id: ID of the user (for authorization)
        void_reason: Optional reason for voiding

    Returns:
        The voided medication log

    Raises:
        HTTPException: If log not found or doesn't belong to user
    """
    log = await get_medication_log(db, log_id, user_id)

    if log.is_voided:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Log entry is already voided"
        )

    log.is_voided = True
    log.voided_at = datetime.now(timezone.utc)

    # Store void reason in notes if provided
    if void_reason:
        original_notes = log.notes or ""
        log.notes = f"[VOIDED: {void_reason}]\n{original_notes}"

    try:
        await db.commit()
        await db.refresh(log)
        logger.info("Voided medication log %s for user %s", log_id, user_id)
        return log

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Database error voiding medication log: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        ) from e


async def calculate_adherence_stats(
    db: AsyncSession,
    user_id: UUID,
    medication_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> AdherenceStats:
    """
    Calculate adherence statistics for a user's medications.

    Args:
        db: Database session
        user_id: ID of the user
        medication_id: Optional specific medication to analyze
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        Adherence statistics
    """
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Build query conditions
    conditions = [
        MedicationLog.user_id == user_id,
        MedicationLog.is_voided == False,
        MedicationLog.taken_at >= start_date,
        MedicationLog.taken_at <= end_date,
    ]

    if medication_id:
        conditions.append(MedicationLog.medication_id == medication_id)

    # Count by action type
    query = (
        select(
            MedicationLog.action,
            func.count(MedicationLog.id).label("count")
        )
        .where(and_(*conditions))
        .group_by(MedicationLog.action)
    )

    result = await db.execute(query)
    counts = {}
    for row in result:
        action_enum = row.action if isinstance(row.action, LogAction) else LogAction(row.action)
        counts[action_enum] = row.count

    taken_count = counts.get(LogAction.TAKEN, 0)
    skipped_count = counts.get(LogAction.SKIPPED, 0)
    missed_count = counts.get(LogAction.MISSED, 0)
    total_logs = taken_count + skipped_count + missed_count

    # Calculate adherence rate (taken / (taken + missed))
    # Skipped is intentional, so we don't count it against adherence
    denominator = taken_count + missed_count
    adherence_rate = (taken_count / denominator * 100) if denominator > 0 else 0.0

    return AdherenceStats(
        total_logs=total_logs,
        taken_count=taken_count,
        skipped_count=skipped_count,
        missed_count=missed_count,
        adherence_rate=round(adherence_rate, 2),
        period_start=start_date,
        period_end=end_date,
    )


async def get_user_adherence_report(
    db: AsyncSession,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> UserAdherenceReport:
    """
    Generate a comprehensive adherence report for a user.

    Args:
        db: Database session
        user_id: ID of the user
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        Complete adherence report with overall and per-medication stats
    """
    # Calculate overall stats
    overall_stats = await calculate_adherence_stats(
        db, user_id, start_date=start_date, end_date=end_date
    )

    # Get list of medications with logs in the period
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Get distinct medications from logs
    query = (
        select(
            MedicationLog.medication_id,
            MedicationLog.medication_name_snapshot
        )
        .where(
            and_(
                MedicationLog.user_id == user_id,
                MedicationLog.is_voided == False,
                MedicationLog.taken_at >= start_date,
                MedicationLog.taken_at <= end_date,
            )
        )
        .distinct()
    )

    result = await db.execute(query)
    medications = result.all()

    # Calculate stats for each medication
    by_medication = []
    for med_id, med_name in medications:
        stats = await calculate_adherence_stats(
            db,
            user_id,
            medication_id=med_id,
            start_date=start_date,
            end_date=end_date,
        )
        by_medication.append(
            MedicationAdherenceReport(
                medication_id=med_id,
                medication_name=med_name,
                stats=stats,
            )
        )

    # Sort by adherence rate (lowest first to highlight problem areas)
    by_medication.sort(key=lambda x: x.stats.adherence_rate)

    return UserAdherenceReport(
        user_id=user_id,
        overall_stats=overall_stats,
        by_medication=by_medication,
    )


async def get_recent_logs_summary(
    db: AsyncSession,
    user_id: UUID,
    days: int = 7,
) -> dict:
    """
    Get a summary of recent log activity.

    Args:
        db: Database session
        user_id: ID of the user
        days: Number of days to look back

    Returns:
        Dictionary with summary statistics
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            func.count(MedicationLog.id).label("total"),
            func.count(func.distinct(MedicationLog.medication_id)).label("unique_medications"),
            func.max(MedicationLog.taken_at).label("last_log"),
        )
        .where(
            and_(
                MedicationLog.user_id == user_id,
                MedicationLog.is_voided == False,
                MedicationLog.taken_at >= start_date,
            )
        )
    )

    result = await db.execute(query)
    row = result.one()

    return {
        "total_logs": row.total,
        "unique_medications": row.unique_medications,
        "last_log_at": row.last_log,
        "period_days": days,
    }
