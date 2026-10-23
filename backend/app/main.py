from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router
from app.seed import init_db, seed_database
from app.db.migrate import migrate_database
from app.db.database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema, apply migrations, and seed synthetic data
    init_db()
    migrate_database()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "MediWell AI REST API Foundation — condition-aware personalized preventive wellness platform. "
        "Provides synthetic de-identified patient data, wellness protocols, and clinical drift detection."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root_metadata():
    """Root metadata endpoint providing API version, status, and documentation pointers."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "phase": "Phase 1 Foundation",
        "synthetic_mode": True,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
        "patients_endpoint": f"{settings.API_V1_PREFIX}/patients",
    }
