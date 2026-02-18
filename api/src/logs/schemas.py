from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, ConfigDict

from api.src.logs.enums import LogAction, LogSource

class MedicationLogBase(BaseModel):
    """Base schema for medication logs."""

    action: LogAction = LogAction.TAKEN
    source: LogSource = LogSource.MANUAL

    taken_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    dosage_taken: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=5000)
    side_effects: Optional[str] = Field(None, max_length=5000)

    @field_validator("taken_at")
    @classmethod
    def validate_taken_at(cls, v: datetime) -> datetime:
        """
        Ensure taken_at is not in the future.
            - This prevents users from accidentally logging a future time which can mess up analytics.
            - We allow a small leeway (5 minutes) to account for slight clock differences on user devices.
        """
        # Ensure v is timezone-aware before comparing
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        # Allow time to be up to 5 minutes in the future (Leeway Buffer)
        # This prevents crashes if the user's phone is slightly fast.
        if v > now + timedelta(minutes=5):
            raise ValueError("Timestamp cannot be in the future")
        return v


class MedicationLogCreate(MedicationLogBase):
    """Schema for creating a medication log."""
    medication_id: UUID = Field(..., description="ID of the medication (required)")
    reminder_id: Optional[UUID] = None


class MedicationLogUpdate(BaseModel):
    """Schema for updating a medication log (limited fields)."""
    dosage_taken: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=5000)
    side_effects: Optional[str] = Field(None, max_length=5000)


class MedicationLogVoid(BaseModel):
    """Schema for voiding a log entry (marking as error)."""
    void_reason: Optional[str] = Field(None, max_length=500)


class MedicationLogResponse(MedicationLogBase):
    """Response schema for medication log."""
    id: UUID
    user_id: UUID

    medication_id: Optional[UUID] = None
    reminder_id: Optional[UUID] = None

    # Snapshots (Crucial for history)
    medication_name_snapshot: str
    dosage_snapshot: Optional[str] = None

    # Error Correction status
    is_voided: bool
    voided_at: Optional[datetime] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicationLogListResponse(BaseModel):
    """Response schema for list of logs."""
    logs: List[MedicationLogResponse]
    total: int
    page: int
    page_size: int


class AdherenceStats(BaseModel):
    """Statistics for medication adherence."""
    total_logs: int
    taken_count: int
    skipped_count: int
    missed_count: int
    adherence_rate: float  # (Taken + Skipped) / Total usually recommended
    period_start: datetime
    period_end: datetime


class MedicationAdherenceReport(BaseModel):
    """Adherence report for a specific medication."""
    medication_id: Optional[UUID]
    medication_name: str
    stats: AdherenceStats


class UserAdherenceReport(BaseModel):
    """Overall adherence report for a user."""
    user_id: UUID
    overall_stats: AdherenceStats
    by_medication: List[MedicationAdherenceReport]