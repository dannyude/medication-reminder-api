from datetime import date, datetime, time
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field

from api.src.medications.enums import MedicationForm
from api.src.medications.models import FrequencyType


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
    def validate_frequency_logic(self):

        ft = self.frequency_type

        # LOGIC FOR "EVERY X HOURS"
        if ft == FrequencyType.EVERY_X_HOURS:
            # MUST have a value (e.g. 4)
            if not self.frequency_value:
                raise ValueError("frequency_value is required when frequency_type is EVERY_X_HOURS")
            # MUST NOT have a custom list
            self.reminder_times = None


        # LOGIC FOR "CUSTOM" (List Mode)
        elif ft == FrequencyType.CUSTOM:
            # MUST have a list
            if not self.reminder_times:
                raise ValueError("reminder_times list is required when frequency_type is CUSTOM")
            # MUST NOT have a value
            self.frequency_value = None

        # LOGIC FOR PRESETS (Daily, Twice Daily, etc.)
        else:
            # These don't need variables. Wipe them to keep DB clean.
            self.frequency_value = None
            # reminder_times can be optional here (or you can auto-generate them later)

        return self


class MedicationCreate(MedicationBase):
    start_date: date
    start_time: time
    timezone: str = "UTC"

    end_date: date | None = None
    end_time: time | None = None

    reminder_times: Optional[list[time]] = None
    @field_validator("reminder_times")
    @classmethod
    def validate_reminder_times(cls, v: list[time] | None) -> list[time] | None:
        """
        Ensure all times in the list are wall-clock times (no TZ info).
        Example: 08:00:00+01:00 -> 08:00:00
        """
        if v:
            return [t.replace(tzinfo=None) for t in v]
        return v


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

        # Combine start_date and start_time into a UTC datetime.
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
        # Combine end_date and end_time into a UTC datetime
        local_dt = datetime.combine(self.end_date, t)
        return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                "name": "Amoxicillin",
                "dosage": "500mg",
                "form": "Capsule",
                "color": "Red and White",
                "administration_route": "Oral",
                "instructions": "Take with food",

                "frequency_type": "twice_daily",
                "timezone": "Africa/Lagos",
                "start_date": "2026-01-23",
                "start_time": "08:00:00",
                "end_date": "2026-02-02",
                "end_time": "20:00:00",

                "current_stock": 20,
                "low_stock_threshold": 5
                }
            ]
        }
    }

class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    form: Optional[MedicationForm] = None
    color: Optional[str] = Field(None, max_length=50)
    instructions: Optional[str] = None
    frequency_type: Optional[FrequencyType] = None
    frequency_value: Optional[int] = Field(None, ge=1, le=24)

    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None
    timezone: Optional[str] = None

    reminder_times: Optional[list[time]] = None
    @field_validator("reminder_times")
    @classmethod
    def validate_reminder_times(cls, v: list[time] | None) -> list[time] | None:
        """
        Ensure all times in the list are wall-clock times (no TZ info).
        Example: 08:00:00+01:00 -> 08:00:00
        """
        if v:
            return [t.replace(tzinfo=None) for t in v]
        return v

    current_stock: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    # @computed_field
    # @property
    # def is_low_stock(self) -> bool:
    #     stock = self.current_stock or 0
    #     threshold = self.low_stock_threshold or 0
    #     return stock <= threshold
    is_active: Optional[bool] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    # 3. KEEP this to strip accidental timezones from time inputs
    @field_validator("start_time", "end_time")
    @classmethod
    def enforce_native_time(cls, v: time | None) -> time | None:
        if v and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v



class MedicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    dosage: str
    form: Optional[str]
    color: Optional[str]
    instructions: Optional[str]

    frequency_type: str
    frequency_value: Optional[int]

    start_datetime: datetime
    end_datetime: Optional[datetime]
    timezone: str

    current_stock: int
    low_stock_threshold: int

    reminder_times: Optional[list[time]] = None
    @field_validator("reminder_times")
    @classmethod
    def validate_reminder_times(cls, v: list[time] | None) -> list[time] | None:
        """
        Ensure all times in the list are wall-clock times (no TZ info).
        Example: 08:00:00+01:00 -> 08:00:00
        """
        if v:
            return [t.replace(tzinfo=None) for t in v]
        return v


    @computed_field
    @property
    def is_low_stock(self) -> bool:
        stock = self.current_stock
        threshold = self.low_stock_threshold
        return stock <= threshold

    is_active: bool
    created_at: datetime
    updated_at: datetime


    model_config = ConfigDict(from_attributes=True)


# Stock update schema
class MedicationStockUpdate(BaseModel):
    quantity: int = Field(..., description="Positive to add, Negative to remove")
    note: Optional[str] = Field(None, max_length=200)



# pagination schema for medications
class MedicationPaginationResponse(BaseModel):

    total: int
    medications: list[MedicationResponse]
    page: int
    page_size: int
