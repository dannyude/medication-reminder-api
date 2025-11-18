import uuid
from sqlalchemy import String, Text

from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column

from api.src.auth.database import Base

class User(Base):
    """
    Database model for a User.
    This class inherits from Base (declarative_base).
    """
    __tablename__ = "Users"

    id: Mapped[uuid.UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    mobile_number: Mapped[str] = mapped_column(String, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)