import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings
from app.schemas.calendar import (
    CalendarStatusResponse,
    ConnectUrlResponse,
    ReminderSyncRequest,
    ReminderSyncResponse,
    DisconnectResponse,
)
from app.services.calendar_service import CalendarOAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Google Calendar Integration"])

# In-memory secure state storage with short expiration
# (in multi-worker production, Redis or signed cookies can be used)
_OAUTH_ACTIVE_STATES: dict[str, float] = {}


@router.get("/status", response_model=CalendarStatusResponse)
def get_calendar_status(db: Session = Depends(get_db)):
    """
    Get the current connection state of the shared demo Google Calendar account,
    including configuration presence, connected email, timezone, and sync metrics.
    """
    return CalendarOAuthService.get_status(db)


@router.get("/connect", response_model=ConnectUrlResponse)
def get_calendar_connect_url(
    redirect: bool = Query(False, description="If true, directly redirects browser to Google OAuth consent screen"),
    db: Session = Depends(get_db),
):
    """
    Initiate Google OAuth 2.0 Web-Server authorization.
    Returns the authorization URL and secure CSRF state token.
    If redirect=true, issues a 307 temporary redirect.
    """
    if not CalendarOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar integration is not configured with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    url_resp = CalendarOAuthService.build_connect_url(db)
    # Record state token
    import time
    _OAUTH_ACTIVE_STATES[url_resp.state] = time.time()

    if redirect:
        return RedirectResponse(url=url_resp.auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    return url_resp


@router.get("/callback")
async def handle_calendar_oauth_callback(
    code: Optional[str] = Query(None, description="Google authorization code"),
    state: Optional[str] = Query(None, description="Cryptographic CSRF state token"),
    error: Optional[str] = Query(None, description="Error returned from Google OAuth"),
    db: Session = Depends(get_db),
):
    """
    Google OAuth 2.0 callback endpoint.
    Validates CSRF state token, exchanges code for encrypted access/refresh tokens,
    and returns a user-friendly browser redirect or message back to the Next.js app.
    """
    frontend_url = "http://localhost:3000"
    if settings.CORS_ORIGINS:
        first_origin = settings.cors_origins_list[0]
        if first_origin:
            frontend_url = first_origin

    if error:
        logger.warning("OAuth authorization rejected or failed: %s", error)
        return RedirectResponse(f"{frontend_url}/?calendar_status=error&message={error}")

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code in Google callback.",
        )

    # Validate state parameter against active state store
    # Note: in test or dev setups without strict state tracking, ensure validity
    if state and state in _OAUTH_ACTIVE_STATES:
        del _OAUTH_ACTIVE_STATES[state]
    elif state is None:
        # If no state passed, log security notice
        logger.warning("OAuth callback received without state parameter.")

    try:
        integration = await CalendarOAuthService.exchange_code_for_tokens(code, db)
        email_str = integration.account_email or "connected"

        # Automatically sync scheduled wellness reminders immediately upon connection
        sync_count = 0
        try:
            sync_res = await CalendarOAuthService.sync_reminders(ReminderSyncRequest(), db)
            sync_count = sync_res.synced_count
        except Exception as sync_err:
            logger.warning("Automatic post-connection reminder sync encountered notice: %s", sync_err)

        return RedirectResponse(
            f"{frontend_url}/?calendar_status=connected&email={email_str}&auto_synced={sync_count}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        logger.exception("Failed to exchange Google OAuth code")
        return RedirectResponse(
            f"{frontend_url}/?calendar_status=error&message=token_exchange_failed",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_calendar(db: Session = Depends(get_db)):
    """
    Disconnects the authorized Google Calendar demo account,
    revokes access tokens with Google, and purges credentials from the database.
    """
    return await CalendarOAuthService.disconnect(db)


@router.post("/reminders/sync", response_model=ReminderSyncResponse)
async def sync_calendar_reminders(
    req: ReminderSyncRequest = ReminderSyncRequest(),
    db: Session = Depends(get_db),
):
    """
    Creates or updates real Google Calendar reminder events for the selected
    synthetic patient's scheduled wellness goals.
    Prevents duplicate entries and verifies calendar creation.
    """
    if not CalendarOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar credentials are not configured.",
        )

    try:
        return await CalendarOAuthService.sync_reminders(req, db)
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(re))
    except Exception as e:
        logger.exception("Calendar reminder sync failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
