from typing import Annotated
from datetime import timedelta

from fastapi import Depends,HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.auth import security
from api.src.auth.tokens import create_access_token, get_current_active_user
from api.src.users.models import User
from api.src.users.schemas import UserCreate, UserResponse
from api.src.users import crud
from api.src.auth.database import get_session



router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
async def register_user_route(
    user_in: UserCreate, session: AsyncSession = Depends(get_session)
) -> UserResponse:
    user = await crud.register_user(user_in, session)
    return UserResponse(id=user.id, first_name=user.first_name)


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await crud.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create JWT token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub":str(user.id) }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me/", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.delete("/{user_id}")
async def delete_user_route(
    user_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    await crud.delete_user(user_id, session)
    return {"message": "User deleted successfully"}
