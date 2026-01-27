import logging
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.database import get_session
from api.src.auth.dependencies import get_current_active_user
from api.src.auth.redis_rate_limiter import RedisRateLimiter
from api.src.auth.schemas import ChangePasswordSchema, LoginSchema, ForgotPasswordSchema, ResetPasswordSchema, UserResponseSchema
from api.src.auth.security import get_password_hash, verify_password
from api.src.auth.tokens import (
    create_access_token,
    create_refresh_token,
    hash_token,
    store_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from api.src.config import settings
from api.src.users.models import User, UserStatus
from api.src.auth.models import RefreshToken
from api.src.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


# Login endpoint
@router.post("/login")
async def login(
    request: Request,
    credentials: LoginSchema,
    session: AsyncSession = Depends(get_session),
):
    """
    user login endpoint.

    Security features:
    - Validates user credentials.
    - Checks account status (active, suspended, deactivated).
    - Generates access and refresh tokens with session versioning.
    """
    stmt = select(User).where(User.email == credentials.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Login failed: User with email %s not found.", credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning("Login failed: Incorrect password for user %s.", credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Contact support.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # if user is active, generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "session_version": user.session_version},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "session_version": user.session_version},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    await store_refresh_token(
        refresh_token,
        user.id,
        user.session_version,
        request.client.host if request.client else None,
        request.headers.get("User-Agent"),
        session,
    )

    ip = request.client.host if request.client else 'unknown IP'
    logger.info("User %s logged in successfully from %s", user.email, ip)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponseSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            mobile_number=user.mobile_number,
            status=user.status,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
    }


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        session_version = payload.get("session_version", 0)
        token_type = payload.get("type")
        jti = payload.get("jti")

        if not user_id or token_type != "refresh" or not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        try:
            user_id = uuid.UUID(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid user ID in token") from exc

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Refresh token has expired") from exc

    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    # Step 2: Hash the token and look it up in the database
    token_hash = hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await session.execute(stmt)
    token_entry = result.scalar_one_or_none()

    if not token_entry:
        logger.warning("Refresh token not found in DB for user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not recognized. Please log in again.",
        )

    # Step 3: Check if token is revoked
    if token_entry.revoked_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. Please log in again.",
        )

    # Step 4: Check for token reuse
    if token_entry.used_token or token_entry.used_at is not None:
        # Fetch user token and invalidate all sessions
        user_smt = select(User).where(User.id == user_id)
        user = (await session.execute(user_smt)).scalar_one()

        logger.critical(
            "SECURITY ALERT: Refresh token reuse detected for user %s. "
            "Token was already used at %s. Invalidating all sessions.",
            user.email,
            token_entry.used_at
)
        # Invalidate all sessions
        user.session_version += 1
        token_entry.revoked_token = True


        # Revoke all refresh tokens
        stmt = select(RefreshToken).where(RefreshToken.user_id == user.id)
        tokens = (await session.execute(stmt)).scalars().all()
        for t in tokens:
            t.revoked_token = True
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="security violation: Refresh token reuse detected. All sessions have been revoked. Please log in again.",
        )

    # step 5: check token expiry in db
    if token_entry.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )

    # Step 6: Fetch user and validate session version
    user_stmt = select(User).where(User.id == user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="User account is not active")

    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Contact support.",
        )

    # Check session version match
    if user.session_version != session_version:
        logger.info("Session invalidated for user %s: session version mismatch.", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalidated. Please log in again.",
        )

    # If everything is valid, generate new tokens
    token_entry.used_token= True
    token_entry.used_at = datetime.now(timezone.utc)
    await session.flush()

    # Issue new tokens
    new_access_token = create_access_token(
        {"sub": str(user.id), "session_version": user.session_version}
    )

    new_refresh_token = create_refresh_token(
        {"sub": str(user.id), "session_version": user.session_version}
    )


    await store_refresh_token(
        refresh_token=new_refresh_token,
        user_id=user.id,
        session_version=user.session_version,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent") if request.headers else None,
        session=session,
    )

    # 5. Save everything
    await session.commit()

    logger.info("Tokens refreshed successfully for user %s", user.email)

    # 6. Return standard OAuth2 response
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

#Get current user details
@router.get("/me", response_model=UserResponseSchema)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    return UserResponseSchema(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        mobile_number=current_user.mobile_number,
        status=current_user.status,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


# Change password endpoint
@router.post("/change_password")
async def change_password(
    password_data: ChangePasswordSchema,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    # Validate old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )
    # validate new passwords match with each other
    if password_data.new_password != password_data.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match.",
        )
    # Update password and session version
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)

    # Increment session version to invalidate existing sessions
    current_user.session_version += 1

    # Revoke all refresh tokens
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_token.is_(False)
        )
        .values(revoked_token=True, revoked_at=datetime.now(timezone.utc))
    )
    await session.execute(stmt)

    await session.commit()

    # Generate new tokens for current session
    access_token = create_access_token(
        data={"sub": str(current_user.id), "session_version": current_user.session_version},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        data={"sub": str(current_user.id), "session_version": current_user.session_version},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info("Password changed for user %s", current_user.email)

    return {
        "message": "Password changed successfully. All other sessions have been logged out.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Logout from current session
@router.post("/logout")
async def logout(
    refresh_token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):

    """
    Logout from current session.

    This will:
    - Revoke the specific refresh token (server-side)
    - Access token remains valid until expiry (client should delete it)
    - User stays logged in on other devices

    For logging out from all devices, use /logout-all endpoint.
    """

    # Hash and find the token
    token_hash = hash_token(refresh_token)

    # Find the refresh token in the database
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.user_id == current_user.id
    )
    result = await session.execute(stmt)
    token_entry = result.scalar_one_or_none()

    # if token not found or doesn't belong to user
    if not token_entry:
        logger.warning(
            "Logout attempt with invalid/missing token for user %s", current_user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token not found.",
        )

    # Check if token is already revoked
    if token_entry.revoked_token:
        logger.info(
            "Logout attempt with already revoked token for user %s", current_user.email)
        return {
            "message": "Session already logged out."
        }

    # Revoke the refresh token
    if not token_entry.revoked_token:
        token_entry.revoked_token = True
        await session.commit()

        logger.info(
            "User %s logged out from current session. Token created at %s"
            , current_user.email, token_entry.created_at)

    return {
        "detail": "Logged out from current session successfully."
    }


# Logout from all sessions
@router.post("/logout_all")
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Logout from ALL devices (revokes all sessions).

    Requires: Access token only
    Effect: Invalidates all sessions, revokes all refresh tokens
    Use case: User suspects account compromise, changing password
    """

    # Increment session version to invalidate all sessions
    current_user.session_version += 1

    # Revoke all refresh tokens
    stmt = (
        update(RefreshToken).
        where(RefreshToken.user_id == current_user.id,
                RefreshToken.revoked_token.is_(False)
        )
        .values(revoked_token=True,
                used_token=True,
                used_at=datetime.now(timezone.utc)
        )
    )

    result = await session.execute(stmt)
    revoked_count = result.rowcount # type: ignore

    await session.commit()


    logger.info(
        "User %s logged out from all sessions. Total tokens revoked: %d",
        current_user.email,
        revoked_count
    )

    return{
        "message": "Logged out from all sessions successfully.",
        "revoked_count": revoked_count
    }

# Forgot password endpoint
@router.post("/forgot_password")
async def forgot_password(
    request: Request,
    body: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Initiates the password reset process.

    Always returns a success message to prevent email enumeration.
    If the email exists, a reset link is sent to the user's email.
    """

    email = body.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limits
    await RedisRateLimiter.check_password_reset_limit(
        email=email,
        ip_address=client_ip,
    )

    success_message = "If the email exists, a reset link has been sent."


    stmt = select(User).where(User.email == body.email)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user:
        reset_token = create_password_reset_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )

        try:
            user_name = f"{user.first_name} {user.last_name}".strip() or "User"

            # we use background tasks to send email asynchronously
            background_tasks.add_task(
                EmailService.send_password_reset_email,
                email=user.email,
                reset_token=reset_token,
                user_name=user_name,
            )
        except Exception as exc:
            logger.error("Failed to schedule password reset email for %s: %s", user.email, exc)
    else:
        logger.info("Password reset requested for non-existent email: %s", body.email)

    # Record this attempt
    await RedisRateLimiter.record_attempt(
        email=email,
        ip_address=client_ip,
    )

    return {"message": success_message}

# Reset password endpoint
@router.post("/reset_password")
async def reset_password(
    request:ResetPasswordSchema,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Completes password reset using the token.
    Invalidates all previous sessions.
    """
    try:
        user_id = verify_password_reset_token(request.reset_token)
    except HTTPException as exc:
        raise HTTPException(status_code=401,
                            detail="Invalid or expired reset token"
                            ) from exc

    # Find user
    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if new passwords is the same as old password
    if verify_password(request.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password.",
        )

    user.hashed_password = get_password_hash(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.session_version += 1

    # Revoke all refresh tokens
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked_token=True, revoked_at=datetime.now(timezone.utc))
    )
    await session.execute(stmt)
    await session.commit()

    user_name = f"{user.first_name} {user.last_name}"
    background_tasks.add_task(
        EmailService.send_password_changed_notification,
        email=user.email,
        user_name=user_name,
    )

    return {"message": "Password reset successful"}