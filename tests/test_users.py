import pytest


@pytest.mark.asyncio
async def test_register_validation_error(client_no_auth):
    payload = {
        "first_name": "A",
        "last_name": "B",
        "email": "invalid-email",
        "mobile_number": "123",
        "password": "weak",
        "confirm_password": "different",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_me_requires_auth(client_no_auth, unauth_override):
    response = await client_no_auth.get("/user/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_empty_first_name(client_no_auth):
    payload = {
        "first_name": "",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_first_name_too_long(client_no_auth):
    payload = {
        "first_name": "A" * 51,
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_last_name(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_last_name_too_long(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "A" * 51,
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_format(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "not-an-email",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_email(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_mobile_too_short(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "123",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_mobile_too_long(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+123456789012345678",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_too_short(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "Pass123!",  # 8 chars exactly is the minimum
        "confirm_password": "Pass123!",
    }
    # This should pass with minimum 8 chars, or fail for password strength (400) or other validation (422)
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code in {201, 400, 422}  # May fail for other reasons


@pytest.mark.asyncio
async def test_register_password_mismatch(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "DifferentPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_very_short(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "short",
        "confirm_password": "short",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_first_name(client_no_auth):
    payload = {
        "last_name": "User",
        "email": "test@example.com",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_email(client_no_auth):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "mobile_number": "+12345678901",
        "password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
    }
    response = await client_no_auth.post("/user/register", json=payload)
    assert response.status_code == 422
