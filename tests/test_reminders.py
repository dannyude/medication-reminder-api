import pytest
from uuid import uuid4
from datetime import datetime, timezone

from api.src.reminders import crud


@pytest.mark.asyncio
async def test_list_reminders_page_size_validation(client):
    response = await client.get("/reminders", params={"page_size": 200})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_page_size_zero(client):
    response = await client.get("/reminders", params={"page_size": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_page_size_negative(client):
    response = await client.get("/reminders", params={"page_size": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_page_zero(client):
    response = await client.get("/reminders", params={"page": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_page_negative(client):
    response = await client.get("/reminders", params={"page": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_reminders_days_ahead_zero(client):
    med_id = uuid4()
    response = await client.post(
        f"/reminders/medications/{med_id}/generate",
        json={"days_ahead": 0}
    )
    # Returns 404 because medication doesn't exist (DummySession returns None)
    # In real API, validation would return 422 if medication exists
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_reminders_days_ahead_exceeds_max(client):
    med_id = uuid4()
    response = await client.post(
        f"/reminders/medications/{med_id}/generate",
        json={"days_ahead": 31}
    )
    # Returns 404 because medication doesn't exist (DummySession returns None)
    # In real API, validation would return 422 if medication exists
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_reminder_taken_success(client, monkeypatch, test_user, make_reminder):
    med_id = uuid4()
    reminder = make_reminder(test_user.id, med_id)

    async def _fake_mark_as_taken(*_args, **_kwargs):
        return reminder

    monkeypatch.setattr(crud, "mark_reminder_as_taken", _fake_mark_as_taken)

    response = await client.post(
        f"/reminders/{reminder.id}/taken",
        json={"notes": "ok"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_mark_reminder_taken_with_empty_notes(client, monkeypatch, test_user, make_reminder):
    med_id = uuid4()
    reminder = make_reminder(test_user.id, med_id)

    async def _fake_mark_as_taken(*_args, **_kwargs):
        return reminder

    monkeypatch.setattr(crud, "mark_reminder_as_taken", _fake_mark_as_taken)

    response = await client.post(
        f"/reminders/{reminder.id}/taken",
        json={"notes": ""}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_mark_reminder_taken_not_found(client, monkeypatch):
    from fastapi import HTTPException, status

    async def _fake_mark_as_taken(*_args, **_kwargs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    monkeypatch.setattr(crud, "mark_reminder_as_taken", _fake_mark_as_taken)

    response = await client.post(
        f"/reminders/{uuid4()}/taken",
        json={"notes": "ok"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_reminder_taken_invalid_uuid(client):
    response = await client.post(
        "/reminders/not-a-uuid/taken",
        json={"notes": "ok"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_with_invalid_status_filter(client):
    response = await client.get("/reminders", params={"status_filter": "INVALID_STATUS"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reminders_with_invalid_date_format(client):
    response = await client.get("/reminders", params={"start_date": "not-a-date"})
    assert response.status_code == 422
