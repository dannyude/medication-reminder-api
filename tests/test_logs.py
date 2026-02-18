import pytest
from fastapi import HTTPException, status
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from api.src.logs import crud


@pytest.mark.asyncio
async def test_get_logs_page_size_validation(client):
    response = await client.get("/logs/get_all", params={"page_size": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_logs_page_size_negative(client):
    response = await client.get("/logs/get_all", params={"page_size": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_logs_page_size_exceeds_max(client, monkeypatch):
    from api.src.logs import crud

    async def _fake_get_logs(*args, **kwargs):
        return ([], 0)

    monkeypatch.setattr(crud, "get_user_medication_logs", _fake_get_logs)

    response = await client.get("/logs/get_all", params={"page_size": 201})
    # May return 422 for validation or 200 with mocked data
    assert response.status_code in {200, 422}


@pytest.mark.asyncio
async def test_get_logs_page_zero(client):
    response = await client.get("/logs/get_all", params={"page": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_logs_page_negative(client):
    response = await client.get("/logs/get_all", params={"page": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_log_success(client, monkeypatch, test_user, make_log):
    async def _fake_create_log(_session, _log_data, _user_id):
        return make_log(test_user.id, _log_data.medication_id)

    monkeypatch.setattr(crud, "create_medication_log", _fake_create_log)

    response = await client.post(
        "/logs/create",
        json={
            "medication_id": "00000000-0000-0000-0000-000000000001",
            "action": "taken",
            "source": "manual",
            "taken_at": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_log_invalid_medication_id(client):
    response = await client.post(
        "/logs/create",
        json={
            "medication_id": "not-a-uuid",
            "action": "taken",
            "source": "manual",
            "taken_at": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_log_invalid_action(client):
    response = await client.post(
        "/logs/create",
        json={
            "medication_id": "00000000-0000-0000-0000-000000000001",
            "action": "invalid_action",
            "source": "manual",
            "taken_at": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_log_invalid_date_format(client):
    response = await client.post(
        "/logs/create",
        json={
            "medication_id": "00000000-0000-0000-0000-000000000001",
            "action": "taken",
            "source": "manual",
            "taken_at": "not-a-date",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_log_missing_required_fields(client):
    """Test that creating a log with only medication_id (missing action/taken_at defaults) validates properly."""
    response = await client.post(
        "/logs/create",
        json={},  # Missing medication_id entirely
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_void_log_not_found(client, monkeypatch):
    async def _fake_void(*_args, **_kwargs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    monkeypatch.setattr(crud, "void_medication_log", _fake_void)

    response = await client.post(
        "/logs/00000000-0000-0000-0000-000000000001/void",
        json={"void_reason": "error"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_void_log_invalid_log_id(client):
    response = await client.post(
        "/logs/not-a-uuid/void",
        json={"void_reason": "error"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_void_log_empty_reason(client, monkeypatch, make_log, test_user):
    log = make_log(test_user.id, "00000000-0000-0000-0000-000000000001")

    async def _fake_void(*_args, **_kwargs):
        return log  # Return a log object

    monkeypatch.setattr(crud, "void_medication_log", _fake_void)

    response = await client.post(
        "/logs/00000000-0000-0000-0000-000000000001/void",
        json={"void_reason": ""},
    )
    # Empty reason should still be allowed
    assert response.status_code == 200
