from datetime import date, time, timedelta
import pytest

from api.src.medications import crud


@pytest.mark.asyncio
async def test_create_medication_validation_error(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "every_x_hours",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_success(client, monkeypatch, test_user, make_medication):
    async def _fake_create_medication(_session, _user_id, _payload):
        return make_medication(test_user.id)

    async def _fake_generate_reminders_for_medication(*_args, **_kwargs):
        return []

    monkeypatch.setattr(crud, "create_medication", _fake_create_medication)

    from api.src.reminders.reminder_generator import ReminderGenerator
    monkeypatch.setattr(ReminderGenerator, "generate_reminders_for_medication", _fake_generate_reminders_for_medication)

    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_medication_empty_name(client):
    payload = {
        "name": "",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_negative_stock(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": -5,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_invalid_timezone(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "INVALID_TIMEZONE",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_invalid_start_time_format(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "25:99",  # Invalid time
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_invalid_reminder_time_format(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["not-a-time"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_invalid_frequency_type(client):
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "invalid_frequency",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_missing_name(client):
    payload = {
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str(date.today()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": ["08:00"],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_medication_missing_reminder_times(client):
    """Test that once_daily without reminder_times works (times are optional for presets)."""
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str((date.today() + timedelta(days=1)).isoformat()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
    }
    response = await client.post("/medications/create", json=payload)
    # Should succeed - reminder_times is optional for presets
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_medication_empty_reminder_times(client):
    """Test that empty reminder_times array is rejected."""
    payload = {
        "name": "Amoxicillin",
        "dosage": "500mg",
        "frequency_type": "once_daily",
        "start_date": str((date.today() + timedelta(days=1)).isoformat()),
        "start_time": "08:00",
        "timezone": "UTC",
        "current_stock": 10,
        "reminder_times": [],
    }
    response = await client.post("/medications/create", json=payload)
    assert response.status_code == 422
