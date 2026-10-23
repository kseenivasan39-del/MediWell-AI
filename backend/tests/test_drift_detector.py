import datetime
import pytest
from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    Habit,
    HabitLog,
    DriftEvent,
    RecoveryProposal,
)
from app.services.drift_detector import (
    calculate_window_dates,
    run_drift_analysis,
)
from app.services.recovery_service import (
    generate_recovery_proposal,
    apply_recovery_decision,
)


# ============================================================================
# 1. Date Windows & Boundaries Tests
# ============================================================================

def test_calculate_window_dates_non_overlapping():
    today = datetime.date(2026, 10, 23)
    b_start, b_end, r_start, r_end = calculate_window_dates(
        as_of_date=today,
        recent_days=7,
        baseline_days=21,
    )
    # Recent: 7 days inclusive: 2026-10-17 to 2026-10-23
    assert r_end == today
    assert r_start == datetime.date(2026, 10, 17)
    assert (r_end - r_start).days + 1 == 7

    # Baseline: 21 days inclusive: 2026-09-26 to 2026-10-16
    assert b_end == datetime.date(2026, 10, 16)
    assert b_start == datetime.date(2026, 9, 26)
    assert (b_end - b_start).days + 1 == 21

    # Guarantee: non-overlapping and contiguous
    assert b_end < r_start
    assert (r_start - b_end).days == 1


# ============================================================================
# 2. Pure Calculation Scenarios (Stable, Threshold, Improving, Sparse)
# ============================================================================

def test_drift_analysis_stable_patient(client):
    """Eleanor Vance: Adherence stable/improving, no drift flagged."""
    res = client.get("/api/v1/patients/SYNTH-T2D-8841/drift")
    assert res.status_code == 200
    data = res.json()
    assert data["has_drift"] is False
    assert data["status"] in ["Stable", "Improving"]
    assert data["data_sufficiency"] == "sufficient"
    assert data["threshold_percentage_points"] == 15.0
    assert len(data["contributing_observations"]) > 0


def test_drift_analysis_active_drift_robert(client):
    """Robert Taylor: Multi-week decline exceeding 15pp threshold."""
    res = client.post(
        "/api/v1/patients/SYNTH-DFT-9905/drift/analyze",
        json={"persist_event": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_drift"] is True
    assert data["status"] == "Active"
    assert data["percentage_point_change"] <= -15.0
    assert data["drift_event_id"] is not None
    assert "exceeds configured alert threshold" in data["explanation"].lower()


def test_drift_analysis_insufficient_baseline_sarah(client):
    """Sarah Jenkins: New onboarding patient, sparse baseline."""
    res = client.get("/api/v1/patients/SYNTH-NEW-1092/drift")
    assert res.status_code == 200
    data = res.json()
    assert data["has_drift"] is False
    assert data["status"] in ["insufficient_data", "no_active_plan"]
    assert data["data_sufficiency"] in ["insufficient_baseline", "no_active_goals"]


def test_drift_analysis_decline_below_threshold(db_session):
    """
    Simulate a custom patient with decline of 10pp (below 15pp threshold).
    Verifies that decline does NOT trigger a drift event.
    """
    today = datetime.date.today()
    # Create test patient
    p = Patient(
        synthetic_identifier="TEST-SUB-THRESH-01",
        display_name="Sub Threshold Test",
        age=45,
        gender="Other",
        primary_condition="General Wellness",
    )
    db_session.add(p)
    db_session.commit()

    plan = WellnessPlan(patient_id=p.id, plan_name="Sub Threshold Plan", status="Active")
    db_session.add(plan)
    db_session.commit()

    habit = db_session.query(Habit).first()
    goal = WellnessGoal(
        plan_id=plan.id,
        habit_id=habit.id,
        title="Daily Walk",
        target_value=30.0,
        frequency="daily",
        priority="high",
        start_date=today - datetime.timedelta(days=40),
    )
    db_session.add(goal)
    db_session.commit()

    # Seed Baseline: 21 days with 18 completions (85.7%)
    b_start, b_end, r_start, r_end = calculate_window_dates(today, 7, 21)
    curr = b_start
    b_day = 0
    while curr <= b_end:
        is_comp = b_day < 18
        log = HabitLog(
            patient_id=p.id,
            habit_id=habit.id,
            log_date=curr,
            is_completed=is_comp,
        )
        db_session.add(log)
        curr += datetime.timedelta(days=1)
        b_day += 1

    # Seed Recent: 7 days with 5 completions (71.4%) -> Drop is 14.3pp (below 15.0pp)
    curr = r_start
    r_day = 0
    while curr <= r_end:
        is_comp = r_day < 5
        log = HabitLog(
            patient_id=p.id,
            habit_id=habit.id,
            log_date=curr,
            is_completed=is_comp,
        )
        db_session.add(log)
        curr += datetime.timedelta(days=1)
        r_day += 1

    db_session.commit()

    analysis = run_drift_analysis(db_session, p.id, as_of_date=today, threshold_percentage_points=15.0)
    assert analysis.has_drift is False
    assert analysis.status == "Stable"
    assert analysis.percentage_point_change == -14.3

    # Clean up test records
    db_session.query(HabitLog).filter(HabitLog.patient_id == p.id).delete()
    db_session.query(WellnessGoal).filter(WellnessGoal.plan_id == plan.id).delete()
    db_session.query(WellnessPlan).filter(WellnessPlan.patient_id == p.id).delete()
    db_session.query(Patient).filter(Patient.id == p.id).delete()
    db_session.commit()


def test_drift_analysis_decline_exactly_at_threshold(db_session):
    """
    Simulate a custom patient with decline of exactly 20.0pp with threshold=20.0pp.
    Verifies that decline >= threshold triggers active drift.
    """
    today = datetime.date.today()
    p = Patient(
        synthetic_identifier="TEST-EXACT-THRESH-01",
        display_name="Exact Threshold Test",
        age=40,
        gender="Other",
        primary_condition="General Wellness",
    )
    db_session.add(p)
    db_session.commit()

    plan = WellnessPlan(patient_id=p.id, plan_name="Exact Plan", status="Active")
    db_session.add(plan)
    db_session.commit()

    habit = db_session.query(Habit).first()
    goal = WellnessGoal(
        plan_id=plan.id,
        habit_id=habit.id,
        title="Daily Hydration",
        target_value=2.0,
        frequency="daily",
        priority="high",
        start_date=today - datetime.timedelta(days=40),
    )
    db_session.add(goal)
    db_session.commit()

    b_start, b_end, r_start, r_end = calculate_window_dates(today, 10, 10)
    # Baseline: 10 days, 8 completed (80.0%)
    curr = b_start
    i = 0
    while curr <= b_end:
        db_session.add(HabitLog(patient_id=p.id, habit_id=habit.id, log_date=curr, is_completed=(i < 8)))
        curr += datetime.timedelta(days=1)
        i += 1

    # Recent: 10 days, 6 completed (60.0%) -> Delta: -20.0pp
    curr = r_start
    i = 0
    while curr <= r_end:
        db_session.add(HabitLog(patient_id=p.id, habit_id=habit.id, log_date=curr, is_completed=(i < 6)))
        curr += datetime.timedelta(days=1)
        i += 1
    db_session.commit()

    analysis = run_drift_analysis(
        db_session,
        p.id,
        as_of_date=today,
        recent_days=10,
        baseline_days=10,
        threshold_percentage_points=20.0,
    )
    assert analysis.has_drift is True
    assert analysis.status == "Active"
    assert analysis.percentage_point_change == -20.0

    # Clean up test records
    db_session.query(HabitLog).filter(HabitLog.patient_id == p.id).delete()
    db_session.query(WellnessGoal).filter(WellnessGoal.plan_id == plan.id).delete()
    db_session.query(WellnessPlan).filter(WellnessPlan.patient_id == p.id).delete()
    db_session.query(Patient).filter(Patient.id == p.id).delete()
    db_session.commit()


# ============================================================================
# 3. Contributing Observations & Barrier Reporting Tests
# ============================================================================

def test_contributing_observations_with_user_barrier(client):
    """Robert Taylor has logged barriers on 2026-10-17 ('Fatigue / prolonged workday')."""
    res = client.get("/api/v1/patients/SYNTH-DFT-9905/drift")
    assert res.status_code == 200
    data = res.json()
    observations = data["contributing_observations"]
    barrier_obs = [o for o in observations if o["category"] == "user_reported_barrier"]
    assert len(barrier_obs) > 0
    assert any("Fatigue" in o["observation"] for o in barrier_obs)
    # Check habit-level decline was identified
    decline_obs = [o for o in observations if o["category"] == "habit_decline"]
    assert len(decline_obs) > 0


def test_contributing_observations_unrecorded_barrier(client):
    """Aisha Patel has high adherence with no barriers reported."""
    res = client.get("/api/v1/patients/SYNTH-ACT-7714/drift")
    assert res.status_code == 200
    data = res.json()
    observations = data["contributing_observations"]
    # Should contain transparent notice inviting user to share context
    unrecorded = [o for o in observations if "unconfirmed" in o["observation"].lower() or "no explicit user barriers" in o["observation"].lower()]
    assert len(unrecorded) > 0


# ============================================================================
# 4. Idempotency & Repeated Analysis Tests
# ============================================================================

def test_repeated_identical_analysis_idempotency(client, db_session):
    """Repeated calls to /drift/analyze must update the existing event without duplicate rows."""
    count_before = db_session.query(DriftEvent).filter(DriftEvent.patient_id == 6).count()

    res1 = client.post("/api/v1/patients/SYNTH-DFT-9905/drift/analyze", json={"persist_event": True})
    assert res1.status_code == 200
    event_id_1 = res1.json()["drift_event_id"]

    res2 = client.post("/api/v1/patients/SYNTH-DFT-9905/drift/analyze", json={"persist_event": True})
    assert res2.status_code == 200
    event_id_2 = res2.json()["drift_event_id"]

    assert event_id_1 == event_id_2
    count_after = db_session.query(DriftEvent).filter(DriftEvent.patient_id == 6).count()
    # Count should not increase infinitely
    assert count_after == count_before or count_after == count_before + 1


def test_drift_history_endpoint(client):
    res = client.get("/api/v1/patients/SYNTH-DFT-9905/drift/history")
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) > 0
    assert "baseline_adherence" in history[0]
    assert "current_adherence" in history[0]


# ============================================================================
# 5. Recovery Proposal Endpoints & Lifecycle Tests
# ============================================================================

def test_create_recovery_proposal_success(client):
    res = client.post("/api/v1/patients/SYNTH-DFT-9905/recovery-proposals")
    assert res.status_code == 201
    proposal = res.json()
    assert proposal["patient_id"] == 6
    assert proposal["status"] == "pending"
    assert len(proposal["proposed_adjustments"]) > 0
    assert "barrier_question" in proposal
    assert proposal["barrier_question"] is not None


def test_list_recovery_proposals_with_filter(client):
    res = client.get("/api/v1/patients/SYNTH-DFT-9905/recovery-proposals?status_filter=pending")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    for p in items:
        assert p["status"] == "pending"


def test_recovery_proposal_decision_accepted(client, db_session):
    """Accepting a proposal adjusts active plan targets and marks drift as Acknowledged."""
    # 1. Create a fresh proposal for Robert
    create_res = client.post("/api/v1/patients/SYNTH-DFT-9905/recovery-proposals")
    proposal_id = create_res.json()["id"]

    # 2. Accept proposal
    decision_payload = {
        "decision": "accepted",
        "decision_notes": "Agreed to ease targets for next 2 weeks.",
    }
    dec_res = client.post(f"/api/v1/recovery-proposals/{proposal_id}/decision", json=decision_payload)
    assert dec_res.status_code == 200
    updated = dec_res.json()
    assert updated["status"] == "accepted"
    assert updated["decided_at"] is not None

    # 3. Verify duplicate decision rejected
    dup_res = client.post(f"/api/v1/recovery-proposals/{proposal_id}/decision", json=decision_payload)
    assert dup_res.status_code == 400
    assert "already been resolved" in dup_res.json()["detail"].lower()

    # Restore drift event status to Active so downstream tests retain expected active drift fixture
    drift = db_session.query(DriftEvent).filter(DriftEvent.patient_id == 6).first()
    if drift:
        drift.status = "Active"
        db_session.commit()


def test_recovery_proposal_decision_edited(client, db_session):
    """Editing a proposal applies patient-revised targets."""
    create_res = client.post("/api/v1/patients/SYNTH-DFT-9905/recovery-proposals")
    proposal = create_res.json()
    proposal_id = proposal["id"]
    first_goal_id = proposal["proposed_adjustments"][0]["goal_id"]

    decision_payload = {
        "decision": "edited",
        "decision_notes": "Customized target to 12 minutes.",
        "user_revised_targets": [
            {
                "goal_id": first_goal_id,
                "revised_target": 12.0,
                "revised_frequency": "daily",
                "notes": "Patient-selected target",
            }
        ],
    }
    dec_res = client.post(f"/api/v1/recovery-proposals/{proposal_id}/decision", json=decision_payload)
    assert dec_res.status_code == 200
    updated = dec_res.json()
    assert updated["status"] == "edited"
    assert len(updated["user_revised_targets"]) == 1
    assert updated["user_revised_targets"][0]["revised_target"] == 12.0

    # Restore drift event status to Active so downstream tests retain expected active drift fixture
    drift = db_session.query(DriftEvent).filter(DriftEvent.patient_id == 6).first()
    if drift:
        drift.status = "Active"
        db_session.commit()


def test_recovery_proposal_decision_rejected(client, db_session):
    create_res = client.post("/api/v1/patients/SYNTH-DFT-9905/recovery-proposals")
    proposal_id = create_res.json()["id"]

    decision_payload = {
        "decision": "rejected",
        "decision_notes": "Prefers current routine without changes.",
    }
    dec_res = client.post(f"/api/v1/recovery-proposals/{proposal_id}/decision", json=decision_payload)
    assert dec_res.status_code == 200
    updated = dec_res.json()
    assert updated["status"] == "rejected"

    # Restore drift event status to Active so downstream tests retain expected active drift fixture
    drift = db_session.query(DriftEvent).filter(DriftEvent.patient_id == 6).first()
    if drift:
        drift.status = "Active"
        db_session.commit()


def test_recovery_proposal_invalid_patient_or_id(client):
    # Invalid patient
    res1 = client.post("/api/v1/patients/NON-EXISTENT/recovery-proposals")
    assert res1.status_code == 404

    # Invalid proposal ID
    res2 = client.post("/api/v1/recovery-proposals/999999/decision", json={"decision": "accepted"})
    assert res2.status_code == 404
