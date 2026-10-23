from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CalendarStatusResponse(BaseModel):
    is_configured: bool = Field(..., description="Whether Google OAuth client credentials are configured")
    is_connected: bool = Field(..., description="Whether a Google Calendar demo account is currently authorized")
    account_email: Optional[str] = Field(None, description="Masked or full authorized Google account email")
    calendar_id: str = Field("primary", description="Configured calendar ID")
    timezone: str = Field("Asia/Kolkata", description="Configured target timezone for reminders")
    connected_at: Optional[datetime] = Field(None, description="Timestamp when authorization succeeded")
    last_synced_at: Optional[datetime] = Field(None, description="Timestamp of the most recent sync attempt")
    last_sync_status: Optional[str] = Field(None, description="'success', 'error', 'partial', or null")
    last_sync_error: Optional[str] = Field(None, description="Last error message if sync failed")
    synced_events_count: int = Field(0, description="Total active event mappings in database")


class ConnectUrlResponse(BaseModel):
    auth_url: str = Field(..., description="Google OAuth 2.0 authorization URL with CSRF state")
    state: str = Field(..., description="Cryptographically random CSRF verification state")


class ReminderSyncGoalItem(BaseModel):
    goal_id: int
    title: str
    habit_name: str
    scheduled_time: str
    custom_time: Optional[str] = None # e.g. "09:00" if goal had no time or user wants to override


class ReminderSyncRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Synthetic patient identifier, e.g. 'SYNTH-DFT-9905'")
    goal_ids: Optional[List[int]] = Field(None, description="Specific goal IDs to sync. If empty, syncs all eligible goals")
    custom_times: Optional[dict[int, str]] = Field(default_factory=dict, description="Mapping of goal_id -> 'HH:MM AM/PM' or 'HH:MM'")


class SyncedEventItem(BaseModel):
    goal_id: int
    google_event_id: str
    title: str
    scheduled_time: str
    html_link: Optional[str] = None
    action: str = Field("created", description="'created', 'updated', or 'skipped'")


class ReminderSyncResponse(BaseModel):
    success: bool
    synced_count: int
    skipped_count: int
    failed_count: int
    events: List[SyncedEventItem] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    delivery_notice: str = Field(
        default="Calendar reminder events created. Note: actual phone/device notifications depend on Google Calendar notification settings, app permissions, synchronization, and device connectivity."
    )


class DisconnectResponse(BaseModel):
    success: bool
    message: str
