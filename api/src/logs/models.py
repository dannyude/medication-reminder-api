import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from api.src.database import Base
from api.src.logs.enums import LogAction

if TYPE_CHECKING:
    from api.src.medications.models import Medication
    from api.src.reminders.models import Reminder
    from api.src.users.models import User

class MedicationLog(Base):
    """
    Records actual medication intake.
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
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    dosage_taken: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    side_effects: Mapped[str | None] = mapped_column(Text)

    action: Mapped[LogAction] = mapped_column(
        SQLEnum(LogAction,native_enum=False),
        default=LogAction.TAKEN,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    medication: Mapped["Medication"] = relationship(
        "Medication",
        back_populates="logs"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="medication_logs"
    )

    reminder: Mapped["Reminder"] = relationship("Reminder")