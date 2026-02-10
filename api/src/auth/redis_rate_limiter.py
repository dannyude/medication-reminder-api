import logging
from fastapi import HTTPException, status

import redis.asyncio as redis

from api.src.config_package import settings

logger = logging.getLogger(__name__)

# Rate limter configuration
MAX_ATTEMPTS = settings.MAX_ATTEMPTS_PER_EMAIL
MAX_ATTEMPTS_IP = settings.MAX_ATTEMPTS_PER_IP
WINDOW_HOURS = settings.WINDOW_HOURS
COOLDOWN_MINUTES = settings.COOLDOWN_MINUTES

redis_client: redis.Redis | None = None

async def init_redis() -> None:
    """
    Docstring for Initialize Redis client for rate limiting.
    """
    global redis_client

    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    # health check
    try:
        ping_result = await redis_client.ping()
        logger.info("Connected to Redis for rate limiting. Ping: %s", ping_result)
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", e)
        raise

async def close_redis():
    """
    Close Redis connection.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")

class RedisRateLimiter:
    @staticmethod
    async def check_password_reset_limit(email: str, ip_address: str | None = None) -> None:
        """
        Check whether password reset rate limits are exceeded.
        Raises HTTPException if blocked.
        """
        if not redis_client:
            logger.warning("Redis not initialized — skipping rate limit check")
            return

        email = email.strip().lower()

        email_key = f"pwd_reset:email:{email}"
        ip_key = f"pwd_reset:ip:{ip_address}" if ip_address else None
        cooldown_key = f"pwd_reset:cooldown:{email}"

        # check cooldown first
        if await redis_client.exists(cooldown_key):
            ttl = await redis_client.ttl(cooldown_key)
            minutes_left = max(1, ttl // 60)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many reset attempts. Try again in {minutes_left} minutes.",
            )

        # Email rate limit check
        email_count = await redis_client.get(email_key)
        if email_count and int(email_count) >= settings.MAX_ATTEMPTS_PER_EMAIL:
            # Activate cooldown
            await redis_client.setex(
                cooldown_key,
                COOLDOWN_MINUTES * 60,
                "1",
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later.",
            )

        # IP rate limit check
        if ip_key:
            ip_count = await redis_client.get(ip_key)
            if ip_count and int(ip_count) >= settings.MAX_ATTEMPTS_PER_IP:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests from this location. Please try again later.",
                )

    @staticmethod
    async def record_attempt(email: str, ip_address: str | None = None) -> None:
        """
        Record a password reset attempt.
        """
        if not redis_client:
            return

        email = email.strip().lower()

        email_key = f"pwd_reset:email:{email}"
        ip_key = f"pwd_reset:ip:{ip_address}" if ip_address else None

        window_seconds = WINDOW_HOURS * 3600

        # Email counter
        await redis_client.incr(email_key)
        await redis_client.expire(email_key, window_seconds, nx=True)

        # IP counter
        if ip_key:
            await redis_client.incr(ip_key)
            await redis_client.expire(ip_key, window_seconds, nx=True)

        logger.info("Password reset attempt recorded for %s", email)