import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.src.users import crud
from api.core.database import get_session
from api.src.users.schemas import UserCreate, UserResponse
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(user_in: UserCreate, session: AsyncSession = Depends(get_session)) -> UserResponse:
    user = await crud.register_user(user_in, session)
    return UserResponse(
        id=user.id,
        first_name=user.first_name
    )

@router.delete("/{user_id}")
async def delete_user_route(user_id: str,session: AsyncSession = Depends(get_session)) -> dict:
    await crud.delete_user(user_id, session)
    return {"message": "User deleted successfully"}