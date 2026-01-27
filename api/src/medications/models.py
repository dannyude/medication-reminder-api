from typing import Optional, Any
import uuid
from datetime import datetime, time, timezone

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)


from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, JSON

from api.src.medications.enums import FrequencyType
from api.src.database import Base



# Helper funtion for reminder times storage
class TimeList(TypeDecorator):
    """
    Saves a list of datetime.time objects as a JSON string in the DB,
    but retrieves them as actual python time objects.
    """

    impl = JSON
    cache_ok = True

    @property
    def python_type(self) -> type:
        """
        Tells SQLAlchemy/Linters that this column acts like a Python list.
        """
        return list

    def process_bind_param(self, value: list[time] | None, dialect: Any) -> list[str] | None:
        if value is None:
            return None
        # Convert [time(8,0), time(20,0)] -> '["08:00:00", "20:00:00"]'
        return [t.strftime("%H:%M:%S") for t in value]

    def process_result_value(self, value: list[str] | None, dialect: Any) -> list[time] | None:
        """Database -> Python (Deserialize)"""
        if value is None:
            return None
        # Convert '["08:00:00", "20:00:00"]' -> [time(8,0), time(20,0)]
        try:
            return [time.fromisoformat(t) for t in value]
        except (ValueError, TypeError):
            return []

    def process_literal_param(self, value: list[time] | None, dialect: Any) -> str:
        """
        Used for rendering literal SQL (e.g. logging/debugging).
        We just reuse the bind param logic.
        """
        if value is None:
            return "NULL"

        return str(self.process_bind_param(value, dialect))





class Medication(Base):
    """
    Represents a prescription or medication plan.
    Example: "Amoxicillin 500mg, Twice Daily"
    """

    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Medication details
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    administration_route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    form: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(50))
    instructions: Mapped[str | None] = mapped_column(Text)

    # Scheduling logic
    frequency_type: Mapped[FrequencyType] = mapped_column(
        SQLEnum(FrequencyType, name="frequency_type", native_enum=False),
        nullable=False,
    )
    frequency_value: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Used when frequency_type = EVERY_X_HOURS",
    )

    # Duration
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timezone
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Inventory
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)

    # Meta
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reminder_times: Mapped[Optional[list[str]]] = mapped_column(
        TimeList,
        nullable=True,
        comment="List of times for daily reminders, stored as comma-separated values",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="medications"
    )

    reminders = relationship(
        "Reminder",
        back_populates="medication",
        cascade="all, delete-orphan",
    )

    logs = relationship(
        "MedicationLog",
        back_populates="medication",
        cascade="all, delete-orphan"
    )
