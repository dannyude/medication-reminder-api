from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from api.src.users.schemas import UserCreate
from api.src.users.models import User, UserStatus
from api.src.auth.security import password_hash

logger = logging.getLogger(__name__)

# Register a new user

async def register_user(user_in: UserCreate, session: AsyncSession) -> User | None:
    """Register a new user in the database."""

    if not user_in.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required.",
        )
    if not user_in.mobile_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number is required.",
        )
    if not user_in.first_name or not user_in.last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First name and last name are required.",
        )


    selected_user = select(User).where(User.email == user_in.email)
    result = await session.execute(selected_user)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    hashed_pw = password_hash.hash(user_in.password.strip())

    db_user = User(
        first_name=user_in.first_name.strip(),
        last_name=user_in.last_name.strip(),
        email=user_in.email.strip().lower(),
        mobile_number=user_in.mobile_number.strip(),
        hashed_password=hashed_pw,
        status=UserStatus.ACTIVE,
        session_version=0,
    )
    session.add(db_user)

    try:
        await session.commit()
        await session.refresh(db_user)
        logger.info("New user created: %s", db_user.email)
        return db_user

    except Exception as exc:
        await session.rollback()

        logger.error("Error creating user: %s", str(exc), exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        ) from exc


# Delete user by ID
async def delete_user(user_id: str, session: AsyncSession) -> None:
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await session.delete(user)
    await session.commit()
