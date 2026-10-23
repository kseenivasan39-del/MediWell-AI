import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    HabitLog,
    Habit,
    Measurement,
    DriftEvent,
    RecoveryProposal,
)
from app.services.wellness_service import (
    get_patient_or_404,
    get_active_plan_for_patient,
    get_adherence_summary,
    compute_habit_momentum,
)
from app.services.drift_detector import run_drift_analysis


def assemble_patient_context(
    db: Session,
    patient_id: str,
    recent_days: int = 14,
) -> Dict[str, Any]:
    """
    Safely retrieves and structures patient health telemetry from the database.
    
    Principles:
    - Never trusts user-supplied health metrics from HTTP payloads.
    - Separates measured facts from user-reported free text.
    - Explicitly marks missing or insufficient data.
    - Does NOT include internal database passwords, API keys, or unrelated records.
    - Includes unit of measurement, date ranges, and observation windows.
    """
    patient = get_patient_or_404(db, patient_id)
    active_plan = get_active_plan_for_patient(db, patient.id)
    today = datetime.date.today()
    recent_start = today - datetime.timedelta(days=recent_days - 1)

    # 1. Goals Context
    goals_data = []
    if active_plan:
        goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
        for g in goals:
            habit = db.query(Habit).filter(Habit.id == g.habit_id).first()
            goals_data.append({
                "goal_id": g.id,
                "habit_id": g.habit_id,
                "habit_name": habit.name if habit else g.title,
                "category": habit.category if habit else "wellness",
                "target": g.target_value,
                "unit": g.target_unit,
                "frequency": g.frequency,
                "recommended_time": g.recommended_time,
                "priority": g.priority,
            })

    # 2. Habit Logs & Barriers in Recent Window
    logs = (
        db.query(HabitLog)
        .filter(
            HabitLog.patient_id == patient.id,
            HabitLog.log_date >= recent_start,
            HabitLog.log_date <= today,
        )
        .order_by(HabitLog.log_date.desc())
        .all()
    )

    logged_days_set = set()
    completed_count = 0
    reported_barriers = []

    for l in logs:
        logged_days_set.add(l.log_date)
        if l.is_completed:
            completed_count += 1
        if l.user_reported_barrier and l.user_reported_barrier.strip():
            habit = db.query(Habit).filter(Habit.id == l.habit_id).first()
            habit_name = habit.name if habit else f"Habit #{l.habit_id}"
            reported_barriers.append({
                "date": str(l.log_date),
                "habit_name": habit_name,
                "barrier_text": l.user_reported_barrier.strip(),
            })

    # 3. Adherence & Momentum (Phase 2 Deterministic Analytics)
    adherence_7d = get_adherence_summary(db, patient.id, window_days=7)
    momentum = compute_habit_momentum(db, patient.id)

    # 4. Drift Analysis (Phase 3 Deterministic Analytics)
    drift_info = None
    try:
        drift_res = run_drift_analysis(db, patient.id, as_of_date=today, persist_event=False)
        drift_info = {
            "has_drift": drift_res.has_drift,
            "status": drift_res.status,
            "baseline_adherence": drift_res.baseline_adherence,
            "recent_adherence": drift_res.recent_adherence,
            "percentage_point_change": drift_res.percentage_point_change,
            "relative_change_pct": drift_res.relative_change_pct,
            "observation_window": f"{drift_res.recent_start_date} to {drift_res.recent_end_date}" if drift_res.recent_start_date else None,
            "data_sufficiency": drift_res.data_sufficiency,
            "explanation": drift_res.explanation,
            "contributing_observations": [
                {
                    "category": o.category,
                    "habit_name": o.habit_name,
                    "observation": o.observation,
                    "evidence_source": o.evidence_source,
                    "date_range": o.date_range,
                    "barrier_reported": o.barrier_reported,
                }
                for o in drift_res.contributing_observations
            ],
        }
    except Exception:
        drift_info = {
            "has_drift": False,
            "status": "Stable",
            "data_sufficiency": "insufficient_data",
            "explanation": "Insufficient telemetry to evaluate drift.",
            "contributing_observations": [],
        }

    # 5. Active Drift Event & Pending Recovery Proposal
    active_drift_orm = (
        db.query(DriftEvent)
        .filter(DriftEvent.patient_id == patient.id, DriftEvent.status == "Active")
        .order_by(DriftEvent.created_at.desc())
        .first()
    )
    pending_proposal = (
        db.query(RecoveryProposal)
        .filter(RecoveryProposal.patient_id == patient.id, RecoveryProposal.status == "pending")
        .order_by(RecoveryProposal.created_at.desc())
        .first()
    )

    # 6. Biomarkers / Clinical Measurements (Latest 3)
    measurements = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient.id)
        .order_by(Measurement.recorded_at.desc())
        .limit(3)
        .all()
    )
    measurements_data = [
        {
            "type": m.measurement_type,
            "value": m.value,
            "unit": m.unit,
            "date": m.recorded_at.strftime("%Y-%m-%d"),
        }
        for m in measurements
    ]

    # Evaluate Data Sufficiency
    if not active_plan:
        data_sufficiency = "no_active_goals"
    elif len(logs) < 5:
        data_sufficiency = "insufficient_history"
    else:
        data_sufficiency = "sufficient"

    return {
        "patient": {
            "id": patient.id,
            "synthetic_identifier": patient.synthetic_identifier,
            "display_name": patient.display_name,
            "age": patient.age,
            "gender": patient.gender,
            "primary_condition": patient.primary_condition,
            "condition_severity": patient.condition_severity,
            "preferences": patient.preferences or {},
            "profile_completeness": patient.profile_completeness,
            "data_quality_rating": patient.data_quality_rating,
        },
        "active_plan": {
            "plan_name": active_plan.plan_name if active_plan else None,
            "version": active_plan.version if active_plan else None,
            "status": active_plan.status if active_plan else "None",
            "goals": goals_data,
        },
        "analytics": {
            "weekly_adherence_percentage": adherence_7d.adherence_percentage,
            "weekly_trend_direction": adherence_7d.trend_direction,
            "habit_momentum_score": momentum.score,
            "habit_momentum_label": momentum.label,
            "streak_days": momentum.streak_days,
            "recent_observation_window": f"{recent_start} to {today}",
            "days_logged_in_window": len(logged_days_set),
            "completed_logs_in_window": completed_count,
        },
        "drift": drift_info,
        "reported_barriers": reported_barriers,
        "recent_biomarkers": measurements_data,
        "active_drift_event_id": active_drift_orm.id if active_drift_orm else None,
        "pending_recovery_proposal": {
            "id": pending_proposal.id,
            "title": pending_proposal.title,
            "proposed_adjustments": pending_proposal.proposed_adjustments,
        } if pending_proposal else None,
        "data_sufficiency": data_sufficiency,
    }
