from email.mime import message
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.auth.database import get_session
from api.src.users.crud import register_user
from api.src.users.schemas import UserCreate, ResponseMessage

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