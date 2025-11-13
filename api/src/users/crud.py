from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.core.database import get_session
from api.src.users.schemas import UserCreate, UserResponse
from api.src.users.models import User
from api.core.security import password_hash


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
    hashed_pw = password_hash.hash(user_in.password)
    db_user = User(
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            email=user_in.email,
            mobile_number=user_in.mobile_number,
            hashed_password=hashed_pw,
        )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


"""Delete a user by ID."""
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