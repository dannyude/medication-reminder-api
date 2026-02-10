from fastapi import APIRouter

from api.src.config_package.settings import settings

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("/frontend")
async def get_frontend_config() -> dict:
    """
    Returns public configuration values for the frontend.
    Only exposes non-sensitive values like Google Client ID.

    Returns:
        dict: Public configuration including google_client_id, frontend_url, and api_url
    """
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "frontend_url": settings.FRONTEND_URL,
        "api_url": "http://localhost:8000"
    }
