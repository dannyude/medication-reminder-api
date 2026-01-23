import logging
from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.users.models import User
from api.src.medications import crud
from api.src.medications.schemas import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse
)

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
    return medication


@router.get("/get_all", response_model=list[MedicationResponse])
async def get_medications(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all medications for current user."""
    medications = await crud.get_user_medications(
        session,
        current_user.id,
        active_only
    )
    return medications


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

@router.patch("/update/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    medication_update: MedicationUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a medication."""
    medication = await crud.update_medication(
        session,
        medication_id,
        current_user.id,
        medication_update
    )
    return medication


@router.delete("/delete/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
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