import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.users.models import User
from api.src.logs import crud
from api.src.logs.enums import LogAction
from api.src.logs.schemas import (
    MedicationLogCreate,
    MedicationLogUpdate,
    MedicationLogVoid,
    MedicationLogResponse,
    MedicationLogListResponse,
    UserAdherenceReport,
)


router = APIRouter(prefix="/logs", tags=["Medication Logs"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=MedicationLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: MedicationLogCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new medication log entry."""
    return await crud.create_medication_log(session, log_data, current_user.id)


@router.get("/get_all", response_model=MedicationLogListResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    medication_id: Optional[UUID] = Query(None),
    action: Optional[LogAction] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_voided: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get medication logs for the current user with filtering and pagination."""
    skip = (page - 1) * page_size
    logs, total = await crud.get_user_medication_logs(
        db=session,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        medication_id=medication_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        include_voided=include_voided,
    )
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/get_specific/{log_id}", response_model=MedicationLogResponse)
async def get_log(
    log_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific medication log by ID."""
    return await crud.get_medication_log(session, log_id, current_user.id)


@router.patch("/{log_id}", response_model=MedicationLogResponse)
async def update_log(
    log_id: UUID,
    update_data: MedicationLogUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a medication log (limited fields)."""
    return await crud.update_medication_log(session, log_id, current_user.id, update_data)


@router.post("/{log_id}/void", response_model=MedicationLogResponse)
async def void_log(
    log_id: UUID,
    void_data: MedicationLogVoid,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Void a medication log (soft delete)."""
    return await crud.void_medication_log(
        session,
        log_id,
        current_user.id,
        void_data.void_reason,
    )


@router.get("/adherence/report", response_model=UserAdherenceReport)
async def get_adherence_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get adherence report for the current user."""
    return await crud.get_user_adherence_report(
        session,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/summary/recent")
async def get_recent_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get summary of recent medication log activity."""
    return await crud.get_recent_logs_summary(session, current_user.id, days)
