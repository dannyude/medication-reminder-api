from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field

from api.src.medications.enums import MedicationForm
from api.src.medications.models import FrequencyType



# SHARED VALIDATORS (DRY Principle)
def normalize_time_list(v: list[time] | None) -> list[time] | None:
    """Strip timezone info from list of times."""
    if v:
        return [t.replace(tzinfo=None) for t in v]
    return v

def normalize_single_time(v: time | None) -> time | None:
    """Strip timezone info from single time."""
    if v and v.tzinfo is not None:
        return v.replace(tzinfo=None)
    return v

def validate_tz_string(v: str | None) -> str | None:
    """Ensure timezone string is valid IANA format."""
    if v is None:
        return None
    try:
        ZoneInfo(v)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Invalid timezone: {v}")
    return v




# medication schemas
class MedicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Medication name")
    dosage: str
    administration_route: str | None = None
    form: str | None = None
    color: str | None = None
    instructions: str | None = None

    frequency_type: FrequencyType
    frequency_value: int | None = None

    current_stock: int = Field(default=0, ge=0, description="Current stock (cannot be negative)")
    low_stock_threshold: int = 5
    is_active: bool = True

    @model_validator(mode='after')
    def validate_frequency_logic(self):
        ft = self.frequency_type

        # 1. EVERY X HOURS (Needs Value, No List)
        if ft == FrequencyType.EVERY_X_HOURS:
            if not self.frequency_value:
                raise ValueError("frequency_value (e.g. 6 hours) is required for 'Every X Hours' frequency type")
            self.reminder_times = None # Times are calculated dynamically, not fixed

        # 2. CUSTOM (Needs List, No Value)
        elif ft == FrequencyType.CUSTOM:
            if not self.reminder_times or len(self.reminder_times) == 0:
                raise ValueError("reminder_times list is required and cannot be empty for 'Custom' frequency")
            self.frequency_value = None

        # 3. PRESETS (Once, Twice, Three, Four Times Daily, As Needed)
        else:
            # Presets should NOT have frequency_value set
            if self.frequency_value is not None:
                raise ValueError(f"frequency_value is only for 'every_x_hours'. Use reminder_times instead for '{ft.value}' frequency")
            # Check if reminder_times is explicitly set to empty list
            if self.reminder_times is not None and len(self.reminder_times) == 0:
                raise ValueError(f"reminder_times cannot be an empty list for '{ft.value}' frequency")
            # ⚠️ Do NOT wipe reminder_times here.
            # If user selects "three_times_daily" and provides custom times, keep them.

        return self


class MedicationCreate(MedicationBase):
    start_date: date
    start_time: time
    timezone: str = "UTC"

    end_date: date | None = None
    end_time: time | None = None

    reminder_times: Optional[list[time]] = None

    # Apply Shared Validators
    _validate_times_list = field_validator("reminder_times")(normalize_time_list)
    _validate_single_time = field_validator("start_time", "end_time")(normalize_single_time)
    _validate_tz = field_validator("timezone")(validate_tz_string)

    @model_validator(mode='after')
    def validate_dates(self):
        start = self.start_date
        end = self.end_date

        # FIX: Compare strictly with today's date (no timedelta minutes logic on dates)
        today = datetime.now(timezone.utc).date()

        if start < today:
            raise ValueError(f"Start date cannot be in the past! (Received: {start}, Today: {today})")

        if end and end < start:
            raise ValueError("End date cannot be before the start date!")

        return self

    @computed_field
    @property
    def start_datetime_utc(self) -> datetime:
        """Converts local start time to UTC for storage."""
        tz = ZoneInfo(self.timezone)
        local_dt = datetime.combine(self.start_date, self.start_time)
        return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

    @computed_field
    @property
    def end_datetime_utc(self) -> datetime | None:
        if not self.end_date:
            return None

        # Default to end of day if no specific end time given
        t = self.end_time or time(23, 59, 59)
        tz = ZoneInfo(self.timezone)

        local_dt = datetime.combine(self.end_date, t)
        return local_dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Amoxicillin",
                "dosage": "500mg",
                "administration_route": "Oral",
                "form": "Capsule",
                "color": "Red and White",
                "instructions": "Take with food",

                "frequency_type": "twice_daily",
                "frequency_value": None,

                "current_stock": 20,
                "low_stock_threshold": 5,

                "timezone": "Africa/Lagos",
                "start_date": "2026-01-31",
                "start_time": "08:00",
                "end_date": "2026-02-10",
                "end_time": "20:00",

                "reminder_times": ["08:00", "20:00"]
            }]
        }
    }




# UPDATE SCHEMA
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

    current_stock: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    # Apply Shared Validators
    _validate_times_list = field_validator("reminder_times")(normalize_time_list)
    _validate_single_time = field_validator("start_time", "end_time")(normalize_single_time)
    _validate_tz = field_validator("timezone")(validate_tz_string)

    @model_validator(mode='after')
    def validate_frequency_logic_on_update(self):
        """Validate frequency_value is only set when frequency_type is 'every_x_hours'."""
        ft = self.frequency_type

        # Only validate if frequency_type was provided in the update
        if ft is None:
            return self

        # 1. EVERY X HOURS (Needs Value, No List)
        if ft == FrequencyType.EVERY_X_HOURS:
            if not self.frequency_value:
                raise ValueError("frequency_value (e.g. 6 hours) is required for 'Every X Hours' frequency type")
            self.reminder_times = None

        # 2. CUSTOM (Needs List, No Value)
        elif ft == FrequencyType.CUSTOM:
            if not self.reminder_times or len(self.reminder_times) == 0:
                raise ValueError("reminder_times list is required and cannot be empty for 'Custom' frequency")
            self.frequency_value = None

        # 3. PRESETS (Once, Twice, Three, Four Times Daily, As Needed)
        else:
            if self.frequency_value is not None:
                raise ValueError(f"frequency_value is only for 'every_x_hours'. Use reminder_times instead for '{ft.value}' frequency")

        return self



# RESPONSE SCHEMA
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

    # 🎨 Computed: Status Helpers
    @computed_field
    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.low_stock_threshold

    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Apply Shared Validators (Clean output for frontend)
    _validate_times_list = field_validator("reminder_times")(normalize_time_list)

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