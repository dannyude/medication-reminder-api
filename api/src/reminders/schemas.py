from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, computed_field

from api.src.medications.enums import ReminderStatus




class ReminderStatusSchema(BaseModel):
    status: ReminderStatus = Field(..., description="taken, missed, skipped")

class MarkAsTakenSchema(BaseModel):
    taken_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the medication was taken. Defaults to current time if not provided."
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Felt good after taking", "No side effects"]
    )

class MarkAsMissedSchema(BaseModel):
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Forgot to take it", "Was feeling unwell"]
    )

class MarkAsSkippedSchema(BaseModel):
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Decided to skip this dose", "Doctor advised to skip"]
    )

# Response Schemas
class ReminderResponse(BaseModel):
    """Schema for reminder responses."""

    id: UUID
    medication_id: UUID
    user_id: UUID
    medication: Any | None = Field(None, exclude=True)

    @computed_field
    @property
    def medication_name(self) -> str:
        if self.medication:
            return getattr(self.medication, "name", "Unknown")
        return "Unknown Medication"

    @computed_field
    @property
    def medication_dosage(self) -> str:
        if self.medication:
            return getattr(self.medication, "dosage", " ")
        return " "

    scheduled_time: datetime
    status: ReminderStatus

    notification_sent_at: Optional[datetime]
    taken_at: Optional[datetime]
    notes: str | None = None

    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

# Paginated List Response
class ReminderListResponse(BaseModel):
    """Paginated list of reminders."""

    total: int
    reminders: list[ReminderResponse]
    page: int
    page_size: int