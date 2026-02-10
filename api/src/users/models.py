from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    String,
    Text,
    DateTime,
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.users.enums import UserStatus
from api.src.database import Base




class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[str] = mapped_column(String(20), nullable=False)

    last_name: Mapped[str] = mapped_column(String(50), nullable=False)

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    mobile_number: Mapped[str | None] = mapped_column(String, nullable=True)

    hashed_password: Mapped[str | None] = mapped_column(Text, nullable=True)

    google_id : Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="TRUE")

    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(UserStatus, name="user_status", values_callable=lambda obj: [e.value for e in obj], native_enum=False, length=50),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    session_version: Mapped[int] = mapped_column(default=0, nullable=False)

    fcm_token: Mapped[str | None] = mapped_column(String, nullable=True)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )




    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    medication_logs = relationship("MedicationLog", back_populates="user", cascade="all, delete-orphan")


    def __repr__(self) -> str:
        return f"<User {self.email}>"

