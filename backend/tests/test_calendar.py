import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.models.wellness import CalendarIntegration, CalendarEventMapping, WellnessGoal, Patient
from app.services.calendar_service import CalendarOAuthService, GOOGLE_CALENDAR_API_BASE
from app.services.crypto import encrypt_token, decrypt_token


@pytest.fixture
def mock_google_creds(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "mock-client-secret-12345")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/calendar/callback")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_ID", "primary")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_TIMEZONE", "Asia/Kolkata")


def test_calendar_status_unconfigured(client, monkeypatch):
    """When credentials are not set, calendar reports is_configured=False and is_connected=False."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")

    res = client.get("/api/v1/calendar/status")
    assert res.status_code == 200
    data = res.json()
    assert data["is_configured"] is False
    assert data["is_connected"] is False
    assert data["calendar_id"] == "primary"
    assert data["timezone"] == "Asia/Kolkata"


def test_calendar_connect_url_generation(client, mock_google_creds):
    """Generates a valid Google OAuth URL containing client_id, scopes, offline access, and CSRF state."""
    res = client.get("/api/v1/calendar/connect")
    assert res.status_code == 200
    data = res.json()
    assert "auth_url" in data
    assert "state" in data
    assert "mock-client-id" in data["auth_url"]
    assert "access_type=offline" in data["auth_url"]
    assert "calendar.events" in data["auth_url"]
    assert data["state"] in data["auth_url"]


def test_calendar_connect_missing_credentials_fails(client, monkeypatch):
    """Cannot generate connect URL if credentials are not configured."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    res = client.get("/api/v1/calendar/connect")
    assert res.status_code == 400
    assert "not configured" in res.json()["detail"]


@pytest.mark.asyncio
async def test_oauth_callback_code_exchange(client, mock_google_creds, db_session):
    """Simulates Google OAuth redirect with valid code; exchanges for tokens and stores encrypted."""
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "mock-access-token-123",
        "refresh_token": "mock-refresh-token-456",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    mock_user_resp = MagicMock()
    mock_user_resp.status_code = 200
    mock_user_resp.json.return_value = {"email": "wellness.demo@gmail.com"}

    mock_event_resp = MagicMock()
    mock_event_resp.status_code = 200
    mock_event_resp.json.return_value = {
        "id": "mock-event-id-callback",
        "htmlLink": "https://calendar.google.com/event?eid=mock",
        "summary": "MediWell AI — Reminder",
    }

    async def mock_post_side_effect(url, *args, **kwargs):
        if "oauth2.googleapis.com/token" in str(url):
            return mock_token_resp
        return mock_event_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post_side_effect), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user_resp

        res = client.get(
            "/api/v1/calendar/callback?code=mock-auth-code&state=mock-state",
            follow_redirects=False,
        )
        assert res.status_code == 302
        assert "calendar_status=connected" in res.headers["location"]
        assert "wellness.demo@gmail.com" in res.headers["location"]

    # Verify database record
    integ = db_session.query(CalendarIntegration).filter_by(provider="google").first()
    assert integ is not None
    assert integ.is_connected is True
    assert integ.account_email == "wellness.demo@gmail.com"
    # Ensure tokens are encrypted at rest
    assert integ.encrypted_access_token != "mock-access-token-123"
    assert decrypt_token(integ.encrypted_access_token) == "mock-access-token-123"
    assert decrypt_token(integ.encrypted_refresh_token) == "mock-refresh-token-456"


@pytest.mark.asyncio
async def test_calendar_disconnect(client, mock_google_creds, db_session):
    """Disconnect clears the persisted credentials and revokes the token."""
    # Ensure integration exists
    integ = db_session.query(CalendarIntegration).filter_by(provider="google").first()
    if not integ:
        integ = CalendarIntegration(
            provider="google",
            is_connected=True,
            encrypted_access_token=encrypt_token("mock-token"),
            account_email="demo@gmail.com",
        )
        db_session.add(integ)
    else:
        integ.is_connected = True
        integ.encrypted_access_token = encrypt_token("mock-token")
        integ.account_email = "demo@gmail.com"
    db_session.commit()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        res = client.post("/api/v1/calendar/disconnect")
        assert res.status_code == 200
        assert res.json()["success"] is True

    db_session.refresh(integ)
    assert integ.is_connected is False
    assert integ.encrypted_access_token is None
    assert integ.account_email is None


@pytest.mark.asyncio
async def test_sync_reminders_creates_and_prevents_duplicates(client, mock_google_creds, db_session):
    """
    Tests syncing reminders:
    1. First sync creates events on Google Calendar and stores mapping.
    2. Hydration/untimed goals without custom time are skipped.
    3. Second sync updates existing mapped events rather than creating duplicates.
    """
    integ = db_session.query(CalendarIntegration).filter_by(provider="google").first()
    if not integ:
        integ = CalendarIntegration(
            provider="google",
            is_connected=True,
            encrypted_access_token=encrypt_token("valid-access-token"),
            encrypted_refresh_token=encrypt_token("valid-refresh-token"),
            token_expiry=datetime.utcnow() + timedelta(hours=1),
            account_email="demo@gmail.com",
        )
        db_session.add(integ)
    else:
        integ.is_connected = True
        integ.encrypted_access_token = encrypt_token("valid-access-token")
        integ.token_expiry = datetime.utcnow() + timedelta(hours=1)
    db_session.commit()

    mock_create_resp = MagicMock()
    mock_create_resp.status_code = 200
    mock_create_resp.json.return_value = {
        "id": "gcal-event-9999",
        "htmlLink": "https://calendar.google.com/event?eid=9999",
        "summary": "MediWell AI — 20-minute Post-Breakfast Brisk Walk",
    }

    mock_update_resp = MagicMock()
    mock_update_resp.status_code = 200
    mock_update_resp.json.return_value = {
        "id": "gcal-event-9999",
        "htmlLink": "https://calendar.google.com/event?eid=9999",
        "summary": "MediWell AI — 20-minute Post-Breakfast Brisk Walk",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.put", new_callable=AsyncMock) as mock_put:
        mock_post.return_value = mock_create_resp
        mock_put.return_value = mock_update_resp

        # Sync Marcus Vance (SYNTH-DFT-9905)
        res = client.post(
            "/api/v1/calendar/reminders/sync",
            json={"patient_id": "SYNTH-DFT-9905"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["synced_count"] >= 1
        # Untimed goals like Hydration Target (2.5L) without explicit time are skipped
        assert data["skipped_count"] >= 1
        assert "delivery_notice" in data

        # Check that event was mapped in DB
        mapping = db_session.query(CalendarEventMapping).filter_by(google_event_id="gcal-event-9999").first()
        assert mapping is not None
        assert mapping.event_title.startswith("MediWell AI —")

        # Second sync should UPDATE the existing mapped event rather than post a duplicate
        res2 = client.post(
            "/api/v1/calendar/reminders/sync",
            json={"patient_id": "SYNTH-DFT-9905"},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        # Verify action was 'updated' for the existing event
        updated_items = [e for e in data2["events"] if e["action"] == "updated"]
        assert len(updated_items) >= 1


@pytest.mark.asyncio
async def test_sync_hydration_with_explicit_custom_time(client, mock_google_creds, db_session):
    """
    Hydration reminders are supported when an explicit schedule is provided in custom_times.
    """
    integ = db_session.query(CalendarIntegration).filter_by(provider="google").first()
    integ.is_connected = True
    integ.encrypted_access_token = encrypt_token("valid-access-token")
    integ.token_expiry = datetime.utcnow() + timedelta(hours=1)
    db_session.commit()

    # Find hydration goal ID
    hydration_goal = db_session.query(WellnessGoal).filter(WellnessGoal.title.like("%Hydration%")).first()
    assert hydration_goal is not None

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "gcal-event-hydration-1",
        "htmlLink": "https://calendar.google.com/event?eid=hydration1",
        "summary": f"MediWell AI — {hydration_goal.title}",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.put", new_callable=AsyncMock) as mock_put:
        mock_post.return_value = mock_resp
        mock_put.return_value = mock_resp

        res = client.post(
            "/api/v1/calendar/reminders/sync",
            json={
                "patient_id": hydration_goal.plan.patient.synthetic_identifier,
                "goal_ids": [hydration_goal.id],
                "custom_times": {str(hydration_goal.id): "11:00 AM"},
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["synced_count"] == 1
        assert data["events"][0]["scheduled_time"] == "11:00"
