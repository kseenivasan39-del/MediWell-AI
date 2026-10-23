from fastapi import APIRouter
from app.api.routes import health, patients, plans, habits, analytics, drift, coach, calendar

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(patients.router)
api_router.include_router(plans.router)
api_router.include_router(habits.router)
api_router.include_router(analytics.router)
api_router.include_router(drift.router)
api_router.include_router(coach.router)
api_router.include_router(calendar.router)
