from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, computed_field

from api.src.medications.enums import ReminderStatus




class MarkReminderSchema(BaseModel):
    """Schema for marking reminder as taken/missed/skipped."""

    status: ReminderStatus = Field(..., description="taken, missed, skipped")
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Took with breakfast"]
    )

    taken_at: Optional[datetime] = Field(
        default=None,
        description="When medication was taken (defaults to now)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "taken",
                "notes": "Took with breakfast",
                "taken_at": None
            }
        }


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




class ReminderListResponse(BaseModel):
    """Paginated list of reminders."""

    total: int
    reminders: list[ReminderResponse]
    page: int
    page_size: int