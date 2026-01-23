import uuid
import enum
from datetime import datetime, timezone

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

from api.src.database import Base


class FrequencyType(str, enum.Enum):
    """How often the medication should be taken."""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_X_HOURS = "every_x_hours"
    AS_NEEDED = "as_needed"
    CUSTOM = "custom"


class ReminderStatus(str, enum.Enum):
    """State of a scheduled reminder."""
    PENDING = "pending"
    SENT = "sent"
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"


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
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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

    # Relationships
    user = relationship("User", back_populates="medications")
    reminders = relationship(
        "Reminder",
        back_populates="medication",
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "MedicationLog",
        back_populates="medication",
        cascade="all, delete-orphan",
    )

# REMINDERS (Scheduled Events)
class Reminder(Base):
    """
    Represents a scheduled reminder event.
    Example: "Take Amoxicillin at 8:00 AM"
    """

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus, name="reminder_status", native_enum=False),
        default=ReminderStatus.PENDING,
        nullable=False,
        index=True,
    )

    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    medication = relationship("Medication", back_populates="reminders")
    user = relationship("User", back_populates="reminders")


# MEDICATION LOG (Audit / History)
class MedicationLog(Base):
    """
    Records actual medication intake.
    Can exist with or without a reminder (e.g., AS_NEEDED).
    """

    __tablename__ = "medication_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reminder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reminders.id", ondelete="SET NULL"),
    )

    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    dosage_taken: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    side_effects: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    medication = relationship("Medication", back_populates="logs")
    user = relationship("User", back_populates="medication_logs")
