import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.wellness import Measurement, WellnessGoal, HabitLog, Habit
from app.schemas.wellness import (
    AdherenceSummary,
    TrendsResponse,
    TrendPoint,
    MeasurementRead,
)
from app.services.wellness_service import (
    get_patient_or_404,
    get_active_plan_for_patient,
    get_adherence_summary,
    compute_adherence,
)

router = APIRouter(tags=["Wellness Analytics"])


@router.get(
    "/patients/{patient_id}/analytics/adherence",
    response_model=AdherenceSummary,
    summary="Retrieve aggregate adherence summary over selectable time windows",
)
def get_patient_adherence(
    patient_id: str,
    window_days: int = Query(7, ge=1, le=180, description="Analysis window in days (e.g. 7, 14, 28, 90)"),
    db: Session = Depends(get_db),
):
    """
    Computes overall adherence percentage and previous-period comparison over 7, 14, 28, or 90 days.
    
    Adherence Rules:
    - Numerator: Completed scheduled habits logged in window.
    - Denominator: Total scheduled goal occurrences in window.
    - Missing days count as non-completed.
    - If patient has no active plan, returns adherence_percentage: null with data_status: "no_active_goals".
    """
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    return get_adherence_summary(db, patient.id, window_days=window_days)


@router.get(
    "/patients/{patient_id}/analytics/trends",
    response_model=TrendsResponse,
    summary="Retrieve day-by-day trend points and category breakdown",
)
def get_patient_trends(
    patient_id: str,
    window_days: int = Query(7, ge=1, le=180, description="Trend window in days (e.g. 7, 14, 28, 90)"),
    db: Session = Depends(get_db),
):
    """
    Returns day-by-day adherence points with per-category breakdowns (activity, nutrition, hydration, etc.)
    Suitable for rendering Recharts time-series area/bar charts.
    """
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    active_plan = get_active_plan_for_patient(db, patient.id)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=window_days - 1)

    if not active_plan:
        return TrendsResponse(
            patient_id=patient.id,
            synthetic_identifier=patient.synthetic_identifier,
            window_days=window_days,
            start_date=start_date,
            end_date=today,
            points=[],
            overall_adherence=None,
            data_status="no_active_plan",
        )

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
    habit_ids = {g.habit_id for g in goals}

    # Fetch all logs in range
    logs = (
        db.query(HabitLog)
        .filter(
            HabitLog.patient_id == patient.id,
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.log_date >= start_date,
            HabitLog.log_date <= today,
        )
        .all()
    )

    # Habit map for categories
    habits = db.query(Habit).filter(Habit.id.in_(habit_ids)).all()
    habit_cat_map = {h.id: h.category for h in habits}

    logs_by_date_and_habit = {(l.log_date, l.habit_id): l.is_completed for l in logs}

    points: List[TrendPoint] = []
    total_scheduled = 0
    total_completed = 0

    curr = start_date
    while curr <= today:
        scheduled_for_day = [
            g for g in goals
            if g.start_date <= curr and (g.end_date is None or g.end_date >= curr)
        ]
        
        day_sched_count = len(scheduled_for_day)
        day_comp_count = 0
        cat_counts: Dict[str, List[int]] = {}

        for g in scheduled_for_day:
            cat = habit_cat_map.get(g.habit_id, "other")
            if cat not in cat_counts:
                cat_counts[cat] = [0, 0] # [scheduled, completed]
            cat_counts[cat][0] += 1

            is_comp = logs_by_date_and_habit.get((curr, g.habit_id), False)
            if is_comp:
                day_comp_count += 1
                cat_counts[cat][1] += 1

        total_scheduled += day_sched_count
        total_completed += day_comp_count

        day_rate = round((day_comp_count / day_sched_count * 100.0), 1) if day_sched_count > 0 else None
        
        breakdown = {}
        for cat, (cat_sched, cat_comp) in cat_counts.items():
            breakdown[cat] = round((cat_comp / cat_sched * 100.0), 1) if cat_sched > 0 else None

        points.append(
            TrendPoint(
                date=curr,
                scheduled_goals=day_sched_count,
                completed_goals=day_comp_count,
                adherence_rate=day_rate,
                category_breakdown=breakdown,
            )
        )
        curr += datetime.timedelta(days=1)

    overall = round((total_completed / total_scheduled * 100.0), 1) if total_scheduled > 0 else None

    return TrendsResponse(
        patient_id=patient.id,
        synthetic_identifier=patient.synthetic_identifier,
        window_days=window_days,
        start_date=start_date,
        end_date=today,
        points=points,
        overall_adherence=overall,
        data_status="sufficient" if len(logs) > 0 else "insufficient_history",
    )


@router.get(
    "/patients/{patient_id}/measurements",
    response_model=List[MeasurementRead],
    summary="List patient measurements with optional type filter",
)
def list_patient_measurements(
    patient_id: str,
    measurement_type: Optional[str] = Query(None, description="e.g. blood_glucose, systolic_bp, weight"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve recorded synthetic vitals and biomarker measurements."""
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    query = db.query(Measurement).filter(Measurement.patient_id == patient.id)
    if measurement_type:
        query = query.filter(Measurement.measurement_type == measurement_type)

    measurements = query.order_by(Measurement.recorded_at.desc()).limit(limit).all()
    return [MeasurementRead.model_validate(m) for m in measurements]
