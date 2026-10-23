import json
import logging
import re
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import zoneinfo

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.wellness import (
    CalendarIntegration,
    CalendarEventMapping,
    WellnessGoal,
    Patient,
)
from app.services.crypto import encrypt_token, decrypt_token
from app.schemas.calendar import (
    CalendarStatusResponse,
    ConnectUrlResponse,
    ReminderSyncRequest,
    ReminderSyncResponse,
    SyncedEventItem,
    DisconnectResponse,
)

logger = logging.getLogger(__name__)

# Google OAuth & Calendar Endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

# Narrowest scope for creating and updating MediWell reminders:
# 'https://www.googleapis.com/auth/calendar.events.owned' creates events owned by the user.
# Fallback standard scope 'https://www.googleapis.com/auth/calendar.events' is standard for primary calendar event management.
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email"


class CalendarOAuthService:
    """
    Manages Google OAuth 2.0 Web-Server flow, token encryption,
    refresh lifecycle, and Calendar event synchronization.
    """

    @staticmethod
    def is_configured() -> bool:
        """Returns True if Google Client ID and Secret are configured."""
        return bool(
            settings.GOOGLE_CLIENT_ID
            and settings.GOOGLE_CLIENT_SECRET
            and settings.GOOGLE_CLIENT_ID != "YOUR_GOOGLE_CLIENT_ID"
        )

    @classmethod
    def get_or_create_integration(cls, db: Session) -> CalendarIntegration:
        """Fetch or initialize the single demo integration record."""
        integration = db.query(CalendarIntegration).filter_by(provider="google").first()
        if not integration:
            integration = CalendarIntegration(
                provider="google",
                calendar_id=settings.GOOGLE_CALENDAR_ID,
                is_connected=False,
            )
            db.add(integration)
            db.commit()
            db.refresh(integration)
        return integration

    @classmethod
    def get_status(cls, db: Session) -> CalendarStatusResponse:
        """Return high-level connection and synchronization status."""
        configured = cls.is_configured()
        integration = db.query(CalendarIntegration).filter_by(provider="google").first()

        synced_count = db.query(CalendarEventMapping).count()

        if not integration or not integration.is_connected:
            return CalendarStatusResponse(
                is_configured=configured,
                is_connected=False,
                account_email=None,
                calendar_id=settings.GOOGLE_CALENDAR_ID,
                timezone=settings.GOOGLE_CALENDAR_TIMEZONE,
                connected_at=None,
                last_synced_at=None,
                last_sync_status=None,
                last_sync_error=None,
                synced_events_count=synced_count,
            )

        return CalendarStatusResponse(
            is_configured=configured,
            is_connected=True,
            account_email=integration.account_email,
            calendar_id=integration.calendar_id or settings.GOOGLE_CALENDAR_ID,
            timezone=settings.GOOGLE_CALENDAR_TIMEZONE,
            connected_at=integration.connected_at,
            last_synced_at=integration.last_synced_at,
            last_sync_status=integration.last_sync_status,
            last_sync_error=integration.last_sync_error,
            synced_events_count=synced_count,
        )

    @classmethod
    def build_connect_url(cls, db: Session) -> ConnectUrlResponse:
        """Generate Google OAuth 2.0 authorization URL with secure CSRF state."""
        if not cls.is_configured():
            raise ValueError("Google OAuth credentials are not configured in backend environment.")

        # Cryptographically secure state
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": CALENDAR_SCOPE,
            "access_type": "offline",
            "prompt": "consent", # Forces refresh_token grant
            "state": state,
            "include_granted_scopes": "true",
        }
        auth_url = f"{GOOGLE_AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
        return ConnectUrlResponse(auth_url=auth_url, state=state)

    @classmethod
    async def exchange_code_for_tokens(
        cls,
        code: str,
        db: Session,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> CalendarIntegration:
        """Exchange authorization code for access and refresh tokens, persist encrypted."""
        if not cls.is_configured():
            raise ValueError("Google OAuth credentials are not configured.")

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with (http_client or httpx.AsyncClient(timeout=15.0)) as client:
            token_res = await client.post(GOOGLE_TOKEN_ENDPOINT, data=data)
            if token_res.status_code != 200:
                logger.error("OAuth token exchange failed: %s", token_res.text)
                raise RuntimeError(f"Google token exchange failed: {token_res.text}")

            tokens = token_res.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in", 3600)
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            # Fetch user email for display
            email = None
            try:
                user_res = await client.get(
                    GOOGLE_USERINFO_ENDPOINT,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if user_res.status_code == 200:
                    email = user_res.json().get("email")
            except Exception as e:
                logger.warning("Could not fetch user email during OAuth exchange: %s", e)

        integration = cls.get_or_create_integration(db)
        integration.account_email = email
        integration.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            integration.encrypted_refresh_token = encrypt_token(refresh_token)
        integration.token_expiry = token_expiry
        integration.scope = tokens.get("scope", CALENDAR_SCOPE)
        integration.is_connected = True
        integration.connected_at = datetime.utcnow()
        integration.last_sync_error = None
        db.commit()
        db.refresh(integration)
        return integration

    @classmethod
    async def get_valid_access_token(
        cls,
        db: Session,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> str:
        """Retrieve valid access token, auto-refreshing via refresh_token if expired."""
        integration = db.query(CalendarIntegration).filter_by(provider="google").first()
        if not integration or not integration.is_connected:
            raise RuntimeError("Calendar integration is not connected.")

        access_token = decrypt_token(integration.encrypted_access_token)
        refresh_token = decrypt_token(integration.encrypted_refresh_token)

        # Check if current access token is valid
        is_expired = False
        if integration.token_expiry:
            if datetime.utcnow() >= integration.token_expiry:
                is_expired = True
        else:
            is_expired = not bool(access_token)

        if not is_expired and access_token:
            return access_token

        # Need to refresh token
        if not refresh_token:
            integration.is_connected = False
            integration.last_sync_error = "Refresh token unavailable. Please reconnect Google Calendar."
            db.commit()
            raise RuntimeError(integration.last_sync_error)

        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with (http_client or httpx.AsyncClient(timeout=15.0)) as client:
            res = await client.post(GOOGLE_TOKEN_ENDPOINT, data=data)
            if res.status_code != 200:
                logger.error("Token refresh failed: %s", res.text)
                integration.is_connected = False
                integration.last_sync_error = f"Token refresh rejected by Google: {res.text}"
                db.commit()
                raise RuntimeError(integration.last_sync_error)

            tokens = res.json()
            new_access_token = tokens.get("access_token")
            expires_in = tokens.get("expires_in", 3600)

            integration.encrypted_access_token = encrypt_token(new_access_token)
            integration.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            if tokens.get("refresh_token"):
                integration.encrypted_refresh_token = encrypt_token(tokens["refresh_token"])
            db.commit()
            return new_access_token

    @classmethod
    async def disconnect(
        cls,
        db: Session,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> DisconnectResponse:
        """Revoke token with Google and clear persisted connection credentials."""
        integration = db.query(CalendarIntegration).filter_by(provider="google").first()
        if not integration or not integration.is_connected:
            return DisconnectResponse(success=True, message="Calendar was not connected.")

        # Attempt token revocation at Google endpoint
        access_token = decrypt_token(integration.encrypted_access_token)
        if access_token:
            try:
                async with (http_client or httpx.AsyncClient(timeout=10.0)) as client:
                    await client.post(
                        GOOGLE_REVOKE_ENDPOINT,
                        params={"token": access_token},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
            except Exception as e:
                logger.warning("Revocation request to Google failed: %s", e)

        integration.is_connected = False
        integration.encrypted_access_token = None
        integration.encrypted_refresh_token = None
        integration.token_expiry = None
        integration.account_email = None
        integration.last_sync_status = None
        integration.last_sync_error = None
        db.commit()

        return DisconnectResponse(
            success=True,
            message="Google Calendar integration disconnected and tokens purged."
        )

    # =========================================================================
    # Reminder Event Synchronization
    # =========================================================================

    @staticmethod
    def parse_time_string(time_str: Optional[str]) -> Optional[Tuple[int, int]]:
        """
        Parses time strings like '08:30 AM', '6:30 PM', '17:30', '12:30 PM'.
        Returns (hour_24, minute) or None if ambiguous/unspecified (e.g. 'Throughout day', 'Mealtimes').
        """
        if not time_str:
            return None
        cleaned = time_str.strip()

        # Try HH:MM AM/PM
        m = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)$", cleaned)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            meridiem = m.group(3).upper()
            if meridiem == "PM" and hour < 12:
                hour += 12
            elif meridiem == "AM" and hour == 12:
                hour = 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        # Try 24-hour HH:MM
        m2 = re.match(r"^(\d{1,2}):(\d{2})$", cleaned)
        if m2:
            hour = int(m2.group(1))
            minute = int(m2.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        return None

    @classmethod
    async def sync_reminders(
        cls,
        req: ReminderSyncRequest,
        db: Session,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ReminderSyncResponse:
        """
        Creates or updates Google Calendar reminder events for eligible patient goals.
        Maps events to prevent duplicates and handles scheduled updates.
        """
        integration = db.query(CalendarIntegration).filter_by(provider="google").first()
        if not integration or not integration.is_connected:
            raise RuntimeError("Google Calendar is not connected. Please authorize first.")

        # Determine patient
        patient = None
        if req.patient_id:
            patient = (
                db.query(Patient)
                .filter(
                    (Patient.synthetic_identifier == req.patient_id)
                    | (Patient.id == (int(req.patient_id) if req.patient_id.isdigit() else -1))
                )
                .first()
            )
        if not patient:
            # Fallback to first synthetic patient
            patient = db.query(Patient).first()

        if not patient:
            raise ValueError("No eligible patient found for reminder sync.")

        # Query wellness goals for this patient's active plans
        goals_query = (
            db.query(WellnessGoal)
            .join(WellnessGoal.plan)
            .filter(WellnessGoal.plan.has(patient_id=patient.id))
        )
        if req.goal_ids:
            goals_query = goals_query.filter(WellnessGoal.id.in_(req.goal_ids))

        goals = goals_query.all()

        tz_str = settings.GOOGLE_CALENDAR_TIMEZONE or "Asia/Kolkata"
        try:
            tz = zoneinfo.ZoneInfo(tz_str)
        except Exception:
            tz = zoneinfo.ZoneInfo("UTC")

        access_token = await cls.get_valid_access_token(db, http_client=http_client)

        synced_events: List[SyncedEventItem] = []
        errors: List[str] = []
        skipped_count = 0

        now_in_tz = datetime.now(tz)
        # Target tomorrow for reminders, or today if scheduled time is later today
        base_date = now_in_tz.date()

        calendar_id = urllib.parse.quote(integration.calendar_id or "primary")
        cal_api_url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/{calendar_id}/events"

        async with (http_client or httpx.AsyncClient(timeout=20.0)) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            for goal in goals:
                # Determine time: custom time override (by int or str goal_id) > goal.recommended_time
                custom_dict = req.custom_times or {}
                time_str = custom_dict.get(goal.id) or custom_dict.get(str(goal.id)) or goal.recommended_time
                parsed_time = cls.parse_time_string(time_str)

                # Hydration / non-timed goals requirement:
                # "Do not create events for goals with no valid schedule without asking the user for a time."
                # "Support hydration reminders only when a schedule has been explicitly configured."
                if not parsed_time:
                    skipped_count += 1
                    continue

                hour, minute = parsed_time
                event_start = datetime(
                    year=base_date.year,
                    month=base_date.month,
                    day=base_date.day,
                    hour=hour,
                    minute=minute,
                    tzinfo=tz,
                )
                # If time has passed today, schedule for tomorrow
                if event_start <= now_in_tz:
                    event_start += timedelta(days=1)
                event_end = event_start + timedelta(minutes=30)

                # Formulate calendar event title and description
                # Requirement: "Prefix titles with MediWell AI —. Include goal name, concise description, synthetic-demo labeling."
                event_title = f"MediWell AI — {goal.title}"
                description = (
                    f"MediWell AI Preventive Wellness Reminder\n\n"
                    f"Habit / Goal: {goal.title}\n"
                    f"Target: {goal.target_value or ''} {goal.target_unit or ''}\n"
                    f"Frequency: {goal.frequency}\n"
                    f"Context: Synthetic Demo Profile ({patient.display_name})\n\n"
                    f"Notification Note: Reminders are subject to device sync and Calendar app notification permissions."
                )

                event_body = {
                    "summary": event_title,
                    "description": description,
                    "start": {
                        "dateTime": event_start.isoformat(),
                        "timeZone": tz_str,
                    },
                    "end": {
                        "dateTime": event_end.isoformat(),
                        "timeZone": tz_str,
                    },
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 10},
                            {"method": "popup", "minutes": 0},
                        ],
                    },
                }

                # Check if mapping already exists for this goal in this calendar
                existing_mapping = (
                    db.query(CalendarEventMapping)
                    .filter_by(goal_id=goal.id, calendar_id=integration.calendar_id or "primary")
                    .first()
                )

                try:
                    if existing_mapping:
                        # Update existing Google Calendar event
                        update_url = f"{cal_api_url}/{existing_mapping.google_event_id}"
                        res = await client.put(update_url, json=event_body, headers=headers)

                        # If 404 (event was deleted on Google Calendar), recreate it
                        if res.status_code == 404:
                            res = await client.post(cal_api_url, json=event_body, headers=headers)
                            action = "created"
                        elif res.status_code == 200:
                            action = "updated"
                        else:
                            errors.append(f"Goal '{goal.title}' update failed ({res.status_code}): {res.text}")
                            continue
                    else:
                        # Create new Google Calendar event
                        res = await client.post(cal_api_url, json=event_body, headers=headers)
                        action = "created"

                    if res.status_code in (200, 201):
                        event_data = res.json()
                        google_event_id = event_data.get("id")

                        # Persist mapping in DB
                        if existing_mapping:
                            existing_mapping.google_event_id = google_event_id
                            existing_mapping.event_title = event_title
                            existing_mapping.scheduled_time = f"{hour:02d}:{minute:02d}"
                            existing_mapping.timezone = tz_str
                            existing_mapping.sync_status = "synced"
                            existing_mapping.last_synced_at = datetime.utcnow()
                        else:
                            mapping = CalendarEventMapping(
                                goal_id=goal.id,
                                patient_id=patient.id,
                                google_event_id=google_event_id,
                                calendar_id=integration.calendar_id or "primary",
                                event_title=event_title,
                                scheduled_time=f"{hour:02d}:{minute:02d}",
                                timezone=tz_str,
                                sync_status="synced",
                                last_synced_at=datetime.utcnow(),
                            )
                            db.add(mapping)

                        synced_events.append(
                            SyncedEventItem(
                                goal_id=goal.id,
                                google_event_id=google_event_id,
                                title=event_title,
                                scheduled_time=f"{hour:02d}:{minute:02d}",
                                html_link=event_data.get("htmlLink"),
                                action=action,
                            )
                        )
                    else:
                        errors.append(f"Goal '{goal.title}' sync failed ({res.status_code}): {res.text}")
                except Exception as ex:
                    logger.exception("Error syncing goal %s to calendar", goal.id)
                    errors.append(f"Goal '{goal.title}' error: {str(ex)}")

        # Update integration sync metrics
        integration.last_synced_at = datetime.utcnow()
        if errors and not synced_events:
            integration.last_sync_status = "error"
            integration.last_sync_error = "; ".join(errors[:3])
        elif errors:
            integration.last_sync_status = "partial"
            integration.last_sync_error = "; ".join(errors[:3])
        else:
            integration.last_sync_status = "success"
            integration.last_sync_error = None

        db.commit()

        return ReminderSyncResponse(
            success=len(synced_events) > 0 or (skipped_count > 0 and not errors),
            synced_count=len(synced_events),
            skipped_count=skipped_count,
            failed_count=len(errors),
            events=synced_events,
            errors=errors,
        )
