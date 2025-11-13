import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.src.users import crud
from api.core.database import get_session
from api.src.users.schemas import UserCreate
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user_route(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session)
    ) -> dict:
    """Register a new user."""
    db_user = await crud.register_user(user_in, session)
    return {"message": "User registered successfully", "user_id": str(db_user.id)}

@router.delete("/{user_id}")
async def delete_user_route(
    user_id: str,
    session: AsyncSession = Depends(get_session)
    ) -> dict:
    """Delete a user by ID."""
    await crud.delete_user(user_id, session)
    return {"message": "User deleted successfully"}