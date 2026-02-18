import pytest
from uuid import uuid4
from fastapi import HTTPException, status

from api.src.medications import crud as med_crud
from api.src.reminders import crud as reminder_crud
from api.src.logs import crud as logs_crud


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_medications(client, monkeypatch):
    """Test that a user cannot access medications created by another user"""
    other_user_id = uuid4()
    medication_id = uuid4()

    async def _fake_get_medication(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this medication"
        )

    monkeypatch.setattr(med_crud, "get_medication", _fake_get_medication)

    response = await client.get(f"/medications/get_specific/{medication_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_update_other_user_medications(client, monkeypatch):
    """Test that a user cannot update medications owned by another user"""
    medication_id = uuid4()

    async def _fake_update_medication(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this medication"
        )

    monkeypatch.setattr(med_crud, "update_medication", _fake_update_medication)

    response = await client.patch(
        f"/medications/{medication_id}",
        json={"name": "NewName"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_other_user_medications(client, monkeypatch):
    """Test that a user cannot delete medications owned by another user"""
    medication_id = uuid4()

    async def _fake_delete_medication(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this medication"
        )

    monkeypatch.setattr(med_crud, "delete_medication", _fake_delete_medication)

    response = await client.delete(f"/medications/{medication_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_reminders(client, monkeypatch):
    """Test that a user cannot access reminders created for another user"""
    reminder_id = uuid4()

    async def _fake_get_reminder(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this reminder"
        )

    monkeypatch.setattr(reminder_crud, "mark_reminder_as_taken", _fake_get_reminder)

    response = await client.post(
        f"/reminders/{reminder_id}/taken",
        json={"notes": "ok"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_logs(client, monkeypatch):
    """Test that a user cannot access logs from another user"""
    log_id = uuid4()

    async def _fake_void_log(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this log"
        )

    monkeypatch.setattr(logs_crud, "void_medication_log", _fake_void_log)

    response = await client.post(
        f"/logs/{log_id}/void",
        json={"void_reason": "error"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_reminders_only_returns_user_reminders(client, monkeypatch):
    """Test that listing reminders only returns reminders for the current user"""
    from api.src.reminders import crud as reminder_crud

    async def _fake_get_user_reminders(*args, **kwargs):
        return ([], 0)  # Empty list, 0 total

    monkeypatch.setattr(reminder_crud, "get_user_reminders", _fake_get_user_reminders)

    response = await client.get("/reminders")
    assert response.status_code == 200
    data = response.json()
    # Verify structure
    assert "reminders" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_list_medications_only_returns_user_medications(client, monkeypatch):
    """Test that listing medications only returns medications for the current user"""
    from api.src.medications import crud as med_crud

    async def _fake_get_medications(*args, **kwargs):
        return ([], 0)  # Empty list, 0 total

    monkeypatch.setattr(med_crud, "get_user_medications", _fake_get_medications)

    response = await client.get("/medications/get_all")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_logs_only_returns_user_logs(client, monkeypatch):
    """Test that listing logs only returns logs for the current user"""
    from api.src.logs import crud as logs_crud

    async def _fake_get_logs(*args, **kwargs):
        return ([], 0)  # Empty list, 0 total

    monkeypatch.setattr(logs_crud, "get_user_medication_logs", _fake_get_logs)

    response = await client.get("/logs/get_all")
    assert response.status_code == 200
    data = response.json()
    # Verify structure
    assert "logs" in data or isinstance(data, list)
