import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.seed import seed_database
from app.models.wellness import Patient, HabitLog

# Test database in memory
# Fixtures are provided by conftest.py


# 1. Health Endpoint Tests
def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "MediWell" in data["app_name"]
    assert data["database"] == "connected"
    assert data["synthetic_mode"] is True


def test_root_metadata_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["phase"] == "Phase 1 Foundation"
    assert data["synthetic_mode"] is True
    assert "/docs" in data["docs_url"]


# 2. Patients Listing Tests
def test_list_patients_returns_all_six_scenarios(client):
    response = client.get("/api/v1/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) == 6

    # Verify key scenarios exist
    identifiers = [p["synthetic_identifier"] for p in patients]
    assert "SYNTH-T2D-8841" in identifiers # Scenario 1: Diabetes
    assert "SYNTH-HTN-4219" in identifiers # Scenario 2: Hypertension
    assert "SYNTH-SLP-3301" in identifiers # Scenario 3: Sleep
    assert "SYNTH-ACT-7714" in identifiers # Scenario 4: Activity
    assert "SYNTH-NEW-1092" in identifiers # Scenario 5: Incomplete profile
    assert "SYNTH-DFT-9905" in identifiers # Scenario 6: Declining adherence

    # Verify scenario 6 flags drift
    robert = next(p for p in patients if p["synthetic_identifier"] == "SYNTH-DFT-9905")
    assert robert["has_active_drift"] is True
    assert robert["display_name"] == "Robert Taylor"


# 3. Patient Retrieval Tests
def test_get_patient_by_id_and_by_identifier(client):
    # Test by integer ID
    response = client.get("/api/v1/patients/1")
    assert response.status_code == 200
    p1 = response.json()
    assert p1["id"] == 1
    assert p1["synthetic_identifier"] == "SYNTH-T2D-8841"
    assert p1["primary_condition"] == "Type 2 Diabetes Mellitus"
    assert p1["active_plan"] is not None
    assert len(p1["active_plan"]["goals"]) > 0

    # Test by synthetic identifier string
    response2 = client.get("/api/v1/patients/SYNTH-T2D-8841")
    assert response2.status_code == 200
    assert response2.json()["id"] == 1


def test_get_unknown_patient_returns_404(client):
    response = client.get("/api/v1/patients/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    response_str = client.get("/api/v1/patients/NON-EXISTENT-CODE")
    assert response_str.status_code == 404


# 4. Profile Completeness Tests
def test_patient_profile_completeness_endpoint(client):
    # High completeness profile
    res_high = client.get("/api/v1/patients/SYNTH-T2D-8841/profile")
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["profile_completeness"] >= 90
    assert data_high["data_quality_rating"] == "High Quality"
    assert data_high["has_sufficient_history"] is True

    # Incomplete / Sparse profile (Scenario 5)
    res_sparse = client.get("/api/v1/patients/SYNTH-NEW-1092/profile")
    assert res_sparse.status_code == 200
    data_sparse = res_sparse.json()
    assert data_sparse["profile_completeness"] == 42
    assert data_sparse["data_quality_rating"] == "Sparse"
    assert data_sparse["has_sufficient_history"] is False
    assert "7_day_baseline_habit_telemetry" in data_sparse["missing_fields"]


# 5. Drift Adherence Trend Verification (Scenario 6)
def test_declining_adherence_scenario_has_sufficient_dated_logs(db_session):
    robert = db_session.query(Patient).filter(Patient.synthetic_identifier == "SYNTH-DFT-9905").first()
    assert robert is not None

    logs = (
        db_session.query(HabitLog)
        .filter(HabitLog.patient_id == robert.id)
        .order_by(HabitLog.log_date.desc())
        .all()
    )
    # Robert should have 35 days * 3 habits = 105 habit logs
    assert len(logs) == 105

    # Check distinct logged dates
    dates = {l.log_date for l in logs}
    assert len(dates) == 35 # 5 full consecutive weeks of data

    # Verify genuine historical decline:
    # Baseline (older than 14 days) should have high adherence (~80-90%)
    baseline_logs = [l for l in logs if (datetime.date.today() - l.log_date).days >= 14]
    baseline_completed = [l for l in baseline_logs if l.is_completed]
    baseline_rate = len(baseline_completed) / len(baseline_logs)
    assert baseline_rate >= 0.80

    # Recent (past 14 days) should show substantial drop
    recent_logs = [l for l in logs if (datetime.date.today() - l.log_date).days < 14]
    recent_completed = [l for l in recent_logs if l.is_completed]
    recent_rate = len(recent_completed) / len(recent_logs)
    assert recent_rate <= 0.60
    assert (baseline_rate - recent_rate) >= 0.20 # > 20% drop confirms genuine drift pattern


# 6. Database Repeatability Test
def test_database_seeding_is_idempotent(db_session):
    count_before = db_session.query(Patient).count()
    res = seed_database(db_session)
    assert res["newly_seeded_patients"] == 0
    assert db_session.query(Patient).count() == count_before
