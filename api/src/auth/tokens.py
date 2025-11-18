from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from fastapi import Depends, HTTPException, status

from api.src.auth.security import SECERET_KEY, ALGORITHM, oauth2_scheme
from api.src.auth.database import get_session
from api.src.users.models import User


# We create both the create_access_token and the referesh_token functions here.
def create_access_token(data: dict, expires_delta: timedelta | None = None):

    to_encode = data.copy()

    to_encode["type"] = "access"

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECERET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECERET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        toke_type = payload.get("type")
        if toke_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise credentials_exception
    smt = select(User).where(User.id == user_id)
    result = await session.execute(smt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user_id


async def get_current_active_user(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Retrieves the current active user from the database.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format.",
        )

    statement = select(User).where(User.id == user_uuid)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user
