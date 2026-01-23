from datetime import date, datetime, time
from uuid import UUID
import zoneinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from api.src.medications.models import FrequencyType, ReminderStatus


# medication schemas

class MedicationBase(BaseModel):
    name: str
    dosage: str
    administration_route: str | None = None
    form: str | None = None
    color: str | None = None
    instructions: str | None = None

    frequency_type: FrequencyType
    frequency_value: int | None = None

    current_stock: int = 0
    low_stock_threshold: int = 5
    is_active: bool = True


    @model_validator(mode='after')
    def check_frequency_value(self):
        # Ensure frequency_value is provided when frequency_type is EVERY_X_HOURS

        if self.frequency_type == FrequencyType.EVERY_X_HOURS and not self.frequency_value:
            raise ValueError('frequency_value is required when frequency_type is EVERY_X_HOURS')
            # Clear frequency_value if not applicable
        if self.frequency_type != FrequencyType.EVERY_X_HOURS and self.frequency_value:
            self.frequency_value = None
        return self


class MedicationCreate(MedicationBase):
    start_date: date
    start_time: time
    timezone: str = "UTC"

    end_date: date | None = None
    end_time: time | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def enforce_native_time(cls, v: time | None) -> time | None:
        """
        Strips timezone info from the time input.
        Ensures we treat '10:00Z' as just '10:00' (Wall Clock Time).
        """
        if v and v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate that the provided timezone is valid."""
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @computed_field
    @property
    def start_datetime_utc(self) -> datetime:

        tz = ZoneInfo(self.timezone)

        """Combine start_date and start_time into a UTC datetime."""
        local_dt = datetime.combine(self.start_date, self.start_time)
        # Here you would convert local_dt to UTC based on self.timezone
        # For simplicity, assuming timezone is UTC
        return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

    @computed_field
    @property
    def end_datetime_utc(self) -> datetime | None:
        if not self.end_date:
            return None
        t = self.end_time or time(23, 59, 59)

        tz = ZoneInfo(self.timezone)
        """Combine end_date and end_time into a UTC datetime."""
        local_dt = datetime.combine(self.end_date, t)
        return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Amoxicillin",
                    "dosage": "500mg",
                    "frequency_type": "twice_daily",
                    "start_date": "2026-01-23",
                    "start_time": "08:00:00",
                    "timezone": "Africa/Lagos",
                    "current_stock": 20,
                    "low_stock_threshold": 5,
                    "is_active": True,
                }
            ]
        }
    }

class MedicationUpdate(BaseModel):
    name: str | None = None
    dosage: str | None = None
    instructions: str | None = None
    frequency_type: FrequencyType | None = None
    frequency_value: int | None = None
    end_date: datetime | None = None
    is_active: bool | None = None

    @field_validator("end_date")
    @classmethod
    def normalize_to_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure end_date is in UTC."""
        if v is None:
            return v

        if v.tzinfo is None:
            raise ValueError(
                "end_date must include timezone information."
                "Example: 2026-02-01T12:00:00Z"
            )
        return v.astimezone(ZoneInfo("UTC"))


class MedicationResponse(MedicationBase):
    id: UUID
    user_id: UUID

    start_date: datetime
    end_date: datetime | None
    timezone: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Reminder schemas

class ReminderBase(BaseModel):
    scheduled_time: datetime


class ReminderCreate(ReminderBase):
    pass


class ReminderResponse(ReminderBase):
    id: UUID
    medication_id: UUID
    user_id: UUID
    status: ReminderStatus
    notification_sent_at: datetime | None
    taken_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# medication log schemas

class MedicationLogCreate(BaseModel):
    medication_id: UUID
    reminder_id: UUID | None = None
    taken_at: datetime
    dosage_taken: str | None = None
    notes: str | None = None
    side_effects: str | None = None


class MedicationLogResponse(BaseModel):
    id: UUID
    medication_id: UUID
    reminder_id: UUID | None
    user_id: UUID
    taken_at: datetime
    dosage_taken: str | None
    notes: str | None
    side_effects: str | None
    created_at: datetime

    class Config:
        from_attributes = True
