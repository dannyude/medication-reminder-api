import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.auth.dependencies import get_current_active_user
from api.src.database import get_session
from api.src.users.schemas import TokenSchema, UserCreate, ResponseMessage, UserUpdate, UserResponseSchema
from api.src.users.crud import (
    register_user,
    get_user,
    get_user_by_email,
    update_user,
    deactivate_user,
    hard_delete_user,
)
from api.src.users.models import User

router = APIRouter(prefix="/user", tags=["Users"])
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=ResponseMessage,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user.

    Creates a new user account with:
    - Email validation and uniqueness check
    - Mobile number validation and uniqueness check
    - Password hashing
    - Automatic account activation

    Returns the created user data (without password).
    """
    new_user = await register_user(user, session)
    return {
        "message": "User registered successfully",
        "user": new_user
    }


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get the authenticated user's profile."""
    return current_user


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user_by_id_route(
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get a user by ID."""
    return await get_user(user_id, session)


@router.get("/by-email/{email}", response_model=UserResponseSchema)
async def get_user_by_email_route(
    email: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a user by email."""
    return await get_user_by_email(email, session)


@router.patch("/{user_id}", response_model=UserResponseSchema)
async def update_user_route(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a user's profile."""
    return await update_user(user_id, user_update, session)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Soft delete a user (set status to INACTIVE)."""
    await deactivate_user(user_id, session)


@router.delete("/{user_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_user_route(
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Permanently delete a user."""
    await hard_delete_user(user_id, session)


@router.post("/fcm-token")
async def update_fcm_token(
    token_data: TokenSchema,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Save the user's device token for push notifications."""
    current_user.fcm_token = token_data.fcm_token
    session.add(current_user)
    await session.commit()
    return {"message": "FCM Token updated successfully"}