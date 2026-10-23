from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.config import settings
from app.schemas.wellness import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse, summary="Application and database health check")
def health_check(db: Session = Depends(get_db)):
    """Verifies that the FastAPI application and SQLite/PostgreSQL database are operational."""
    db_status = "connected"
    try:
        # Check active connectivity
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthCheckResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=db_status,
        synthetic_mode=True,
    )
