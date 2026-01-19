from datetime import datetime, timedelta, timezone
import uuid
import logging
import hashlib
import jwt

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.auth.security import SECERET_KEY, ALGORITHM
from api.src.users.models import RefreshToken

logger = logging.getLogger(__name__)


# We create both the create_access_token and the referesh_token functions here.
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token with session tracking."""
    to_encode = data.copy()

    now = datetime.now(timezone.utc)

    to_encode.update({
        "sub": str(data.get("sub")),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + (expires_delta or timedelta(minutes=15))).timestamp()
        ),
    })

    return jwt.encode(to_encode, SECERET_KEY, algorithm=ALGORITHM)

# Create refresh token
def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)

    to_encode = {
        **data,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(
            (now + (expires_delta or timedelta(days=7))).timestamp()
        ),
    }

    return jwt.encode(to_encode, SECERET_KEY, algorithm=ALGORITHM)


def hash_token(raw_token: str) -> str:
    """Hash the token using SHA-256 for secure storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()

async def store_refresh_token(
    refresh_token: str,
    user_id: uuid.UUID,
    session_version: int,
    ip_address: str | None,
    user_agent: str | None,
    session: AsyncSession,
) -> None:
    # Decode the token to get expiration and jti
    payload = jwt.decode(refresh_token, SECERET_KEY, algorithms=[ALGORITHM])

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing jti",
        )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    token_entry = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(refresh_token),
        jti=jti,
        session_version=session_version,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    try:
        session.add(token_entry)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    logger.info("Refresh token stored for user %s", user_id)



def create_password_reset_token(
    subject: str, expires_delta: timedelta | None = None
) -> str:

    now = datetime.now(timezone.utc)

#   Create password reset token
    payload = {
        "sub": subject,
        "type": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + (expires_delta or timedelta(minutes=15))).timestamp()
        ),
    }
    return jwt.encode(
        payload,
        SECERET_KEY,
        algorithm=ALGORITHM,
    )

def verify_password_reset_token(encoded_token: str) -> uuid.UUID:
    """Verify password reset token and return user ID."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired password reset token",
    )
    try:
        payload = jwt.decode(encoded_token, SECERET_KEY, algorithms=[ALGORITHM])

        token_type: str | None = payload.get("type")
        user_id: str | None = payload.get("sub")
        issued_at: int | None = payload.get("iat")

        if token_type != "password_reset" or not user_id:
            raise credentials_exception

        if not isinstance(issued_at, int):
            raise credentials_exception

        if not user_id:
            raise credentials_exception

        try :
            user_uuid = uuid.UUID(user_id)
        except ValueError as exc:
            raise credentials_exception from exc

        return user_uuid

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password reset token has expired",
        ) from exc

    except jwt.PyJWTError as exc:
        raise credentials_exception from exc