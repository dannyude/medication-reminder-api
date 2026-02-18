import pytest


@pytest.mark.asyncio
async def test_login_invalid_credentials(client_no_auth):
    payload = {
        "email": "missing@example.com",
        "password": "WrongPassword1!",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code in {401, 422}


@pytest.mark.asyncio
async def test_refresh_invalid_token(client_no_auth):
    response = await client_no_auth.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_empty_email(client_no_auth):
    payload = {
        "email": "",
        "password": "ValidPass123!",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code in {401, 422}


@pytest.mark.asyncio
async def test_login_invalid_email_format(client_no_auth):
    payload = {
        "email": "not-an-email",
        "password": "ValidPass123!",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code in {401, 422}


@pytest.mark.asyncio
async def test_login_empty_password(client_no_auth):
    payload = {
        "email": "test@example.com",
        "password": "",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code in {401, 422}


@pytest.mark.asyncio
async def test_login_missing_email(client_no_auth):
    payload = {
        "password": "ValidPass123!",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_password(client_no_auth):
    payload = {
        "email": "test@example.com",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_missing_token(client_no_auth):
    response = await client_no_auth.post("/auth/refresh", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_empty_token(client_no_auth):
    response = await client_no_auth.post("/auth/refresh", json={"refresh_token": ""})
    assert response.status_code in {401, 422}


@pytest.mark.asyncio
async def test_refresh_malformed_token(client_no_auth):
    response = await client_no_auth.post("/auth/refresh", json={"refresh_token": "not.a.jwt"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_extra_fields(client_no_auth):
    payload = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "extra_field": "should_be_ignored",
    }
    response = await client_no_auth.post("/auth/login", json=payload)
    # Should either pass or fail validation depending on config
    assert response.status_code in {401, 422}
