import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.src.users.schemas import UserCreate, UserUpdate
from api.src.users.models import User, UserStatus
from api.src.auth.security import password_hash

logger = logging.getLogger(__name__)


# CREATE USER
async def register_user(user_in: UserCreate, session: AsyncSession) -> User:
    """
    Register a new user in the database.

    Performs the following steps:
    1. Validates required fields (email, mobile, name)
    2. Checks for existing user with same email
    3. Hashes password using bcrypt
    4. Creates user with ACTIVE status
    5. Persists to database with transaction handling

    Args:
        user_in: UserCreate schema with user details
        session: Async database session

    Returns:
        The created User object

    Raises:
        HTTPException 400: If validation fails or email already exists
        HTTPException 500: If database operation fails

    Example:
        new_user = await register_user(
            user_in=UserCreate(
                email="john@example.com",
                password="secure_password",
                first_name="John",
                last_name="Doe",
                mobile_number="1234567890"
            ),
            session=session
        )
    """

    # 1. Validate Required Fields
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

    # 2. Check for Duplicate Email
    selected_user = select(User).where(User.email == user_in.email.strip().lower())
    result = await session.execute(selected_user)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # 3. Hash Password
    hashed_pw = password_hash.hash(user_in.password.strip())

    # 4. Create User Object
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

    # 5. Persist to Database
    try:
        await session.commit()
        await session.refresh(db_user)
        logger.info("New user registered: %s", db_user.email)
        return db_user

    except Exception as exc:
        await session.rollback()
        logger.error("Error registering user: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        ) from exc


# READ USER
async def get_user(user_id: UUID, session: AsyncSession) -> User:
    """
    Fetch a user by ID.

    Args:
        user_id: The user's UUID
        session: Async database session

    Returns:
        The User object

    Raises:
        HTTPException 404: If user not found

    Example:
        user = await get_user(user_id=uuid, session=session)
    """
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

# READ USER BY EMAIL
async def get_user_by_email(email: str, session: AsyncSession) -> User:
    """
    Fetch a user by email address.

    Args:
        email: The user's email
        session: Async database session

    Returns:
        The User object

    Raises:
        HTTPException 404: If user not found

    Example:
        user = await get_user_by_email(email="john@example.com", session=session)
    """
    statement = select(User).where(User.email == email.strip().lower())
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# UPDATE USER
async def update_user(user_id: UUID, user_update: UserUpdate, session: AsyncSession) -> User:
    """
    Update a user's profile information.

    Only updates fields that are explicitly set in the update schema.
    Passwords are handled separately through a dedicated password change endpoint.

    Args:
        user_id: The user's UUID
        user_update: UserUpdate schema with fields to update
        session: Async database session

    Returns:
        The updated User object

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If email is taken by another user
        HTTPException 500: If database operation fails

    Example:
        updated_user = await update_user(
            user_id=user_id,
            user_update=UserUpdate(first_name="Jane"),
            session=session
        )
    """
    # 1. Fetch the user
    user = await get_user(user_id, session)

    # 2. Get update data (exclude unset fields)
    update_data = user_update.model_dump(exclude_unset=True)

    # 3. Check for email conflicts if email is being changed
    if "email" in update_data and update_data["email"] != user.email:
        email_stmt = select(User).where(
            User.email == update_data["email"].strip().lower()
        )
        result = await session.execute(email_stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use by another user",
            )
        # Normalize email
        update_data["email"] = update_data["email"].strip().lower()

    # 4. Apply updates
    for field, value in update_data.items():
        if value is not None:
            # Normalize string fields
            if isinstance(value, str):
                value = value.strip()
            setattr(user, field, value)

    # 5. Persist changes
    try:
        await session.commit()
        await session.refresh(user)
        logger.info("User updated: %s", user.email)
        return user

    except Exception as exc:
        await session.rollback()
        logger.error("Error updating user %s: %s", user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        ) from exc


# DELETE USER (Soft Delete)
async def deactivate_user(user_id: UUID, session: AsyncSession) -> None:
    """
    Soft delete a user by marking their status as DEACTIVATED.

    This preserves user data for audit/compliance purposes while making the
    account inaccessible. To permanently delete, use hard_delete_user.

    Args:
        user_id: The user's UUID
        session: Async database session

    Raises:
        HTTPException 404: If user not found
        HTTPException 500: If database operation fails

    Example:
        await deactivate_user(user_id=user_id, session=session)
        # User is now DEACTIVATED but data is preserved
    """
    user = await get_user(user_id, session)

    try:
        user.status = UserStatus.DEACTIVATED
        await session.commit()
        logger.info("User deactivated: %s", user.email)

    except Exception as exc:
        await session.rollback()
        logger.error("Error deactivating user %s: %s", user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        ) from exc


async def hard_delete_user(user_id: UUID, session: AsyncSession) -> None:
    """
    Permanently delete a user from the database.

    WARNING: This completely removes the user record. Use with caution.
    Prefer delete_user for most cases to preserve audit trail.

    Args:
        user_id: The user's UUID
        session: Async database session

    Raises:
        HTTPException 404: If user not found
        HTTPException 500: If database operation fails

    Example:
        await hard_delete_user(user_id=user_id, session=session)
        # User is permanently removed
    """
    user = await get_user(user_id, session)

    try:
        await session.delete(user)
        await session.commit()
        logger.warning("User permanently deleted: %s", user_id)

    except Exception as exc:
        await session.rollback()
        logger.error("Error permanently deleting user %s: %s", user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to permanently delete user"
        ) from exc
