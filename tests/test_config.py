import pytest


@pytest.mark.asyncio
async def test_get_frontend_config(client_no_auth):
    response = await client_no_auth.get("/config/frontend")
    assert response.status_code == 200
    data = response.json()
    assert "google_client_id" in data
    assert "frontend_url" in data
    assert "api_url" in data
