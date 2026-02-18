import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from api.src.database import Base
from api.src.logs.enums import LogAction, LogSource

if TYPE_CHECKING:
    from api.src.medications.models import Medication
    from api.src.reminders.models import Reminder
    from api.src.users.models import User

class MedicationLog(Base):
    """
    Records actual medication intake history.
    This table is an immutable log of actions.
    """
    __tablename__ = "medication_logs"

    # 1. Performance: Composite index for timeline queries
    __table_args__ = (
        Index("idx_med_logs_user_taken", "user_id", "taken_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # 2. Safety: ondelete="SET NULL" prevents historical data loss if Med is deleted
    medication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 3. Snapshot: Preserves name & dosage even if Medication is deleted/renamed
    medication_name_snapshot: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of medication at the time of intake"
    )

    # [NEW] Snapshot the dosage too (e.g., if they later change dose to 100mg, this keeps "50mg")
    dosage_snapshot: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Dosage strength at the time of intake"
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

    # 4. Analytics: Track where this log came from
    source: Mapped[LogSource] = mapped_column(
        SQLEnum(LogSource, native_enum=False),
        default=LogSource.MANUAL,
        nullable=False
    )

    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    dosage_taken: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    side_effects: Mapped[str | None] = mapped_column(Text)

    action: Mapped[LogAction] = mapped_column(
        SQLEnum(LogAction, native_enum=False),
        default=LogAction.TAKEN,
        nullable=False,
    )

    # [NEW] Error Correction: Allow users to "undo" a log without deleting the record
    is_voided: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if this log entry was made in error and 'deleted' by user"
    )

    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # 5. Integrity: Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    medication: Mapped["Medication"] = relationship(
        "Medication",
        back_populates="logs"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="medication_logs"
    )

    reminder: Mapped["Reminder"] = relationship("Reminder")