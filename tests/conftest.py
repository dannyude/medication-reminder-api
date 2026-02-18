from __future__ import annotations

from datetime import datetime, timezone, time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict
from httpx import AsyncClient
from httpx import ASGITransport

from main import app
from api.src.auth.dependencies import get_current_active_user
from api.src.database import get_session
from api.src.users.models import UserStatus


class _FakeScalars:
    def __init__(self, data=None):
        self.data = data or []

    def all(self):
        return self.data


class _FakeResult:
    def __init__(self, data=None):
        self.data = data or []

    def scalar_one_or_none(self):
        return self.data[0] if self.data else None

    def scalar(self):
        return self.data[0] if self.data else 0

    def scalars(self):
        return _FakeScalars(self.data)

    def all(self):
        return self.data


class DummySession:
    async def execute(self, *_args, **_kwargs):
        return _FakeResult([])

    async def commit(self) -> None:
        return None

    async def refresh(self, instance, *_args, **_kwargs) -> None:
        # Simulate generating an ID and timestamps if missing
        if not hasattr(instance, "id") or instance.id is None:
            instance.id = uuid4()
        if not hasattr(instance, "created_at") or instance.created_at is None:
            instance.created_at = datetime.now(timezone.utc)
        # Fix: Check if updated_at is None, not just if attribute exists
        if not hasattr(instance, "updated_at") or instance.updated_at is None:
            instance.updated_at = datetime.now(timezone.utc)
        return None

    def add(self, instance) -> None:
        if not hasattr(instance, "id") or instance.id is None:
            instance.id = uuid4()
        if not hasattr(instance, "created_at") or instance.created_at is None:
            instance.created_at = datetime.now(timezone.utc)
        return None

    def add_all(self, instances) -> None:
        for instance in instances:
            self.add(instance)

    async def rollback(self) -> None:
        return None





@pytest.fixture
def test_user():
    return SimpleNamespace(
        id=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        mobile_number="+12345678901",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        last_login_at=None,
    )


@pytest.fixture
def override_auth(test_user):
    async def _override_get_current_active_user():
        return test_user

    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    yield
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def override_session():
    async def _override_get_session():
        yield DummySession()

    app.dependency_overrides[get_session] = _override_get_session
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def client(override_auth, override_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client_no_auth(override_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def unauth_override():
    async def _override_get_current_active_user():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    yield
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def make_medication():
    def _make(user_id):
        now = datetime.now(timezone.utc)
        return SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            name="Amoxicillin",
            dosage="500mg",
            form=None,
            color=None,
            instructions=None,
            frequency_type="once_daily",
            frequency_value=None,
            start_datetime=now,
            end_datetime=None,
            timezone="UTC",
            current_stock=10,
            low_stock_threshold=5,
            reminder_times=[time(8, 0)],
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    return _make


@pytest.fixture
def make_reminder():
    def _make(user_id, medication_id):
        now = datetime.now(timezone.utc)
        med = SimpleNamespace(name="Amoxicillin", dosage="500mg")
        return SimpleNamespace(
            id=uuid4(),
            medication_id=medication_id,
            user_id=user_id,
            medication=med,
            scheduled_time=now,
            status="pending",
            notification_sent_at=None,
            taken_at=None,
            notes=None,
            created_at=now,
            updated_at=None,
        )

    return _make


@pytest.fixture
def make_log():
    def _make(user_id, medication_id):
        now = datetime.now(timezone.utc)
        return SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            medication_id=medication_id,
            reminder_id=None,
            medication_name_snapshot="Amoxicillin",
            dosage_snapshot="500mg",
            action="taken",
            source="manual",
            taken_at=now,
            dosage_taken="500mg",
            notes=None,
            side_effects=None,
            is_voided=False,
            voided_at=None,
            created_at=now,
        )

    return _make
