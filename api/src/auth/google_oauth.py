import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from api.src.config_package import settings
from api.src.database import get_session
from api.src.auth.schemas import GoogleLoginSchema, TokenResponse
from api.src.auth.tokens import create_access_token, create_refresh_token
from api.src.users.models import User
from api.src.services.email.service import EmailService

logger = logging.getLogger(__name__)



GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

async def google_login(
    token_schema: GoogleLoginSchema,
    session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    try:
        # 1. Verify the token with Google's Certificates
        # This checks the signature, expiration, and issuer.
        id_info = id_token.verify_oauth2_token(
            token_schema.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )

        # 2. Security Check: Audience
        # Ensure this token was issued SPECIFICALLY for your app, not someone else's.
        if id_info['aud'] != GOOGLE_CLIENT_ID:
            raise ValueError('Could not verify audience.')

        # 3. Extract verified data
        email = id_info.get('email')
        google_id = id_info.get('sub')  # 'sub' is the unique Google User ID
        # picture = id_info.get('picture')
        email_verified = id_info.get('email_verified')
        first_name = id_info.get('given_name', 'unknown')
        last_name = id_info.get('family_name', 'unknown')

        if not email_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email not verified.")

    except ValueError as e:
        # Token is invalid, expired, or faked
        logger.warning("Invalid Google token attempt: %s", str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google Token") from e

    # 4. Check Database (Login or Register logic)
    account_linked = False
    is_new_user = False

    try:
        # Use SELECT FOR UPDATE to prevent race condition
        stmt = select(User).filter(User.email == email).with_for_update()
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            # CASE A: User exists
            if not user.google_id:
                # 🔗 ACCOUNT LINKING: User signed up with Email/Pass before, now using Google.
                # Trust Google (since email is verified) and link the account.
                user.google_id = google_id
                account_linked = True
                logger.info("Linked Google account for existing user: %s", email)
        else:
            # CASE B: New User -> Create them
            user = User(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                hashed_password=None,  # No password since they use Google OAuth
            )
            session.add(user)
            is_new_user = True
            logger.info("Created new user via Google OAuth: %s", email)

        await session.commit()
        await session.refresh(user)

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("Database error during Google login: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        ) from e

    # Send emails AFTER successful database commit
    # This way, email failures won't affect authentication
    if account_linked:
        try:
            await EmailService.send_account_linked_notification(
                email=user.email,
                user_name=user.email.split('@')[0]
            )
        except Exception as e:
            # Don't fail the login if email fails
            logger.error("Failed to send account linking notification: %s", str(e))

    if is_new_user:
        try:
            await EmailService.send_welcome_email(
                email=user.email,
                user_name=user.email.split('@')[0]
            )
        except Exception as e:
            # Don't fail the login if email fails
            logger.error("Failed to send welcome email: %s", str(e))

    # 5. Issue YOUR App's Tokens
    # The frontend now forgets about Google and uses these tokens for your API.
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "session_version": user.session_version
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "session_version": user.session_version
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )