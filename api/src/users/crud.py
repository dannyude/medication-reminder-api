from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from api.core.database import get_session
from api.src.users.schemas import UserCreate, UserResponse
from api.src.users.models import User
from api.core.security import password_hash


async def register_user(user_in: UserCreate, session=Depends(get_session)) -> UserResponse:

    try:
        statement = select(User).where(User.email == user_in.email)
        existing_user_result = await session.execute(statement)
        if existing_user_result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )
        # 2. Hash the password
        hashed_pass = password_hash.hash(user_in.password)
        # 3. Create the database User object
        db_user = User(
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            email=user_in.email,
            mobile_number=user_in.mobile_number,
            hashed_password=hashed_pass,
        )
        # 4. Add to session and commit
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering the user.",
        ) from e

"""Delete a user by ID."""
async def delete_user(user_id: str, session=Depends(get_session)) -> None:
    try:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        await session.delete(user)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the user.",
        ) from e