from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.src.users.schemas import UserCreate, UserResponse
from api.src.users.models import User
from api.src.auth.security import password_hash

# Register a new user
async def register_user(user_in: UserCreate, session: AsyncSession) -> UserResponse:
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
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


# Authenticate user by email and password
async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not password_hash.verify(password, user.hashed_password):
        return None
    return user


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
