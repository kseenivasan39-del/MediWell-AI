import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.seed import seed_database
from app.models.wellness import Patient, WellnessPlan, WellnessGoal, HabitLog, Habit

# Fixtures are provided by conftest.py


# ============================================================================
# 1. Dashboard Endpoint Tests
# ============================================================================

def test_dashboard_complete_profile_eleanor(client):
    """Scenario 1: Eleanor Vance (Complete diabetes profile, reviewed plan)."""
    response = client.get("/api/v1/patients/SYNTH-T2D-8841/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["patient"]["display_name"] == "Eleanor Vance"
    assert data["patient"]["primary_condition"] == "Type 2 Diabetes Mellitus"
    assert data["plan_status"] == "Active"
    assert data["active_plan"] is not None
    assert data["active_plan"]["plan_name"] == "Metabolic Stabilization & Glycemic Guard v3"

    # Today's goals
    assert data["today_goals"]["total"] > 0
    assert "completion_percentage" in data["today_goals"]

    # Adherence & momentum
    assert data["weekly_adherence"]["current_week_percentage"] is not None
    assert data["habit_momentum"]["score"] is not None
    assert "formula_documented" in data["habit_momentum"]

    # Measurements & completeness
    assert len(data["recent_measurements"]) > 0
    assert data["profile_completeness"]["profile_completeness"] >= 90
    assert data["drift_detector"]["status"] in ["Active", "Stable"]


def test_dashboard_declining_adherence_robert(client):
    """Scenario 6: Robert Taylor (Multi-week decline, active drift)."""
    response = client.get("/api/v1/patients/SYNTH-DFT-9905/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["patient"]["display_name"] == "Robert Taylor"
    assert data["drift_detector"]["has_drift"] is True
    assert data["drift_detector"]["status"] == "Active"
    assert data["drift_detector"]["percentage_point_change"] == -27.0
    assert data["drift_detector"]["recovery_suggestion"] is not None


def test_dashboard_incomplete_profile_sarah(client):
    """Scenario 5: Sarah Jenkins (Sparse data, onboarding state, plan Under Review)."""
    response = client.get("/api/v1/patients/SYNTH-NEW-1092/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["patient"]["display_name"] == "Sarah Jenkins"
    assert data["profile_completeness"]["profile_completeness"] == 42
    assert data["profile_completeness"]["data_quality_rating"] == "Sparse"
    # When baseline is insufficient or plan is Under Review, drift detector is inactive
    assert data["drift_detector"]["has_drift"] is False
    assert data["drift_detector"]["status"] in ["No Active Plan", "Unavailable - Insufficient Baseline"]


def test_dashboard_unknown_patient_returns_404(client):
    response = client.get("/api/v1/patients/NON-EXISTENT/dashboard")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# 2. Wellness Plan Endpoints Tests
# ============================================================================

def test_list_patient_plans(client):
    response = client.get("/api/v1/patients/SYNTH-HTN-4219/plans")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) >= 1
    assert plans[0]["plan_name"] == "Cardiovascular Resilience & DASH Protocol"


def test_get_patient_active_plan(client):
    response = client.get("/api/v1/patients/SYNTH-HTN-4219/plans/active")
    assert response.status_code == 200
    plan = response.json()
    assert plan["status"] == "Active"
    assert len(plan["goals"]) >= 3


def test_get_plan_by_id(client):
    response = client.get("/api/v1/plans/1")
    assert response.status_code == 200
    plan = response.json()
    assert plan["id"] == 1
    assert "goals" in plan


def test_get_unknown_plan_returns_404(client):
    response = client.get("/api/v1/plans/999999")
    assert response.status_code == 404


def test_get_plan_goals(client):
    response = client.get("/api/v1/plans/1/goals")
    assert response.status_code == 200
    goals = response.json()
    assert len(goals) > 0
    assert "priority" in goals[0]


# ============================================================================
# 3. Habits and Daily Goals Endpoints Tests
# ============================================================================

def test_list_patient_habits(client):
    response = client.get("/api/v1/patients/SYNTH-T2D-8841/habits")
    assert response.status_code == 200
    habits = response.json()
    assert len(habits) >= 3
    codes = [h["code"] for h in habits]
    assert "post_meal_walk" in codes


def test_list_today_goals(client):
    response = client.get("/api/v1/patients/SYNTH-T2D-8841/goals/today")
    assert response.status_code == 200
    today_goals = response.json()
    assert len(today_goals) >= 3
    for g in today_goals:
        assert "is_completed_today" in g
        assert "category" in g


# ============================================================================
# 4. Habit Log Creation, Update, and Conflict Handling
# ============================================================================

def test_create_habit_log_success(client, db_session):
    today = datetime.date.today()
    # Check if a log already exists for Sarah Jenkins on today; if not, create one
    post_data = {
        "habit_id": 1, # post_meal_walk
        "log_date": str(today),
        "is_completed": True,
        "numeric_value": 25.0,
        "unit": "min",
        "notes": "Testing habit log creation",
    }
    # Use Sarah Jenkins (patient id 5) who has no post_meal_walk log today
    response = client.post("/api/v1/patients/SYNTH-NEW-1092/habits/logs", json=post_data)
    assert response.status_code == 201
    created = response.json()
    assert created["is_completed"] is True
    assert created["numeric_value"] == 25.0

    # Test Duplicate Entry Prevention (409 Conflict)
    duplicate_res = client.post("/api/v1/patients/SYNTH-NEW-1092/habits/logs", json=post_data)
    assert duplicate_res.status_code == 409
    assert "already exists" in duplicate_res.json()["detail"].lower()


def test_create_habit_log_future_date_rejected(client):
    future_date = datetime.date.today() + datetime.timedelta(days=2)
    post_data = {
        "habit_id": 1,
        "log_date": str(future_date),
        "is_completed": True,
        "numeric_value": 20.0,
    }
    response = client.post("/api/v1/patients/SYNTH-NEW-1092/habits/logs", json=post_data)
    assert response.status_code == 422
    assert "future" in response.json()["detail"].lower()


def test_create_habit_log_negative_value_rejected(client):
    today = datetime.date.today()
    post_data = {
        "habit_id": 2,
        "log_date": str(today),
        "is_completed": True,
        "numeric_value": -10.0,
    }
    response = client.post("/api/v1/patients/SYNTH-NEW-1092/habits/logs", json=post_data)
    assert response.status_code == 422


def test_update_habit_log_with_barrier(client, db_session):
    # Find any log for Eleanor
    log = db_session.query(HabitLog).filter(HabitLog.patient_id == 1).first()
    assert log is not None

    patch_data = {
        "is_completed": False,
        "user_reported_barrier": "Severe fatigue after clinical treatment",
        "notes": "Audited patient entry",
    }
    response = client.patch(f"/api/v1/habit-logs/{log.id}", json=patch_data)
    assert response.status_code == 200
    updated = response.json()
    assert updated["is_completed"] is False
    assert updated["user_reported_barrier"] == "Severe fatigue after clinical treatment"
    assert updated["updated_at"] is not None


def test_update_unknown_habit_log_returns_404(client):
    response = client.patch("/api/v1/habit-logs/999999", json={"is_completed": True})
    assert response.status_code == 404


def test_list_habit_logs_pagination_and_date_filter(client):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=7)
    response = client.get(
        f"/api/v1/patients/SYNTH-DFT-9905/habits/logs?start_date={start}&end_date={today}&page=1&page_size=10"
    )
    assert response.status_code == 200
    paginated = response.json()
    assert paginated["page"] == 1
    assert paginated["page_size"] == 10
    assert len(paginated["items"]) <= 10
    assert paginated["total"] > 0


# ============================================================================
# 5. Wellness Analytics Endpoints Tests
# ============================================================================

def test_patient_adherence_analytics(client):
    response = client.get("/api/v1/patients/SYNTH-HTN-4219/analytics/adherence?window_days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 7
    assert data["adherence_percentage"] is not None
    assert data["adherence_percentage"] > 0.0
    assert data["eligible_occurrences"] > 0


def test_patient_adherence_analytics_28_days(client):
    response = client.get("/api/v1/patients/SYNTH-DFT-9905/analytics/adherence?window_days=28")
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 28
    assert data["adherence_percentage"] is not None
    assert data["trend_direction"] is not None


def test_patient_analytics_trends_recharts_points(client):
    response = client.get("/api/v1/patients/SYNTH-HTN-4219/analytics/trends?window_days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 7
    assert len(data["points"]) == 7
    for pt in data["points"]:
        assert "date" in pt
        assert "scheduled_goals" in pt
        assert "completed_goals" in pt
        assert "category_breakdown" in pt


def test_patient_measurements_endpoint(client):
    response = client.get("/api/v1/patients/SYNTH-T2D-8841/measurements")
    assert response.status_code == 200
    measurements = response.json()
    assert len(measurements) > 0
    assert measurements[0]["measurement_type"] in ["hba1c", "fasting_glucose"]
    assert measurements[0]["value"] > 0
