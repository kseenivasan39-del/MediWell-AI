import datetime
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    HabitLog,
    Habit,
    DriftEvent,
    Measurement,
)
from app.schemas.wellness import (
    AdherenceSummary,
    TrendPoint,
    TrendsResponse,
    GoalTodayRead,
    DashboardGoalsSummary,
    DashboardAdherenceSummary,
    HabitMomentumSummary,
    DriftDetectorSummary,
    PatientDashboardResponse,
    PatientBase,
    PatientProfileCompleteness,
    WellnessPlanRead,
    WellnessGoalRead,
    DriftEventRead,
    MeasurementRead,
)


def get_patient_or_404(db: Session, patient_id: str) -> Patient:
    """Retrieve patient by integer ID or synthetic identifier or raise 404."""
    query = db.query(Patient)
    if patient_id.isdigit():
        p = query.filter(Patient.id == int(patient_id)).first()
    else:
        p = query.filter(Patient.synthetic_identifier == patient_id).first()
    if not p:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found",
        )
    return p


def get_active_plan_for_patient(db: Session, patient_id: int) -> Optional[WellnessPlan]:
    """Retrieve active wellness plan for a patient."""
    return (
        db.query(WellnessPlan)
        .filter(WellnessPlan.patient_id == patient_id, WellnessPlan.status == "Active")
        .first()
    )


def compute_adherence(
    db: Session,
    patient_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Tuple[int, int, Optional[float]]:
    """
    Computes scheduled habit occurrences and completed occurrences in a date range.
    
    Formula and Missing Data Rules:
    - Denominator (Eligible Occurrences): Sum of active goals scheduled on each day within the range.
      A goal is scheduled on a day if start_date <= day and (end_date is None or end_date >= day).
    - Numerator (Completed Occurrences): Logged records in habit_logs with is_completed == True
      corresponding to scheduled habits on those dates.
    - Missing Logs Rule: Days or habits with no habit_log record are counted as NOT COMPLETED (0 in numerator).
      Never assume completion without an explicit log.
    - Zero Denominator Rule: If no goals were scheduled in the window (e.g. newly registered patient with no plan),
      returns (0, 0, None) - explicitly distinguishing 0% adherence from insufficient / unavailable data.
    """
    active_plan = get_active_plan_for_patient(db, patient_id)
    if not active_plan:
        return 0, 0, None

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
    if not goals:
        return 0, 0, None

    habit_ids = {g.habit_id for g in goals}

    # Generate days in range
    days = []
    curr = start_date
    while curr <= end_date:
        days.append(curr)
        curr += datetime.timedelta(days=1)

    if not days:
        return 0, 0, None

    # Calculate eligible occurrences
    total_eligible = 0
    for day in days:
        for g in goals:
            if g.start_date <= day and (g.end_date is None or g.end_date >= day):
                total_eligible += 1

    if total_eligible == 0:
        return 0, 0, None

    # Count completed logs within range for these habits
    completed_logs = (
        db.query(HabitLog)
        .filter(
            HabitLog.patient_id == patient_id,
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.log_date >= start_date,
            HabitLog.log_date <= end_date,
            HabitLog.is_completed == True,
        )
        .count()
    )

    adherence_pct = round((completed_logs / total_eligible) * 100.0, 1)
    return total_eligible, completed_logs, adherence_pct


def get_adherence_summary(
    db: Session,
    patient_id: int,
    window_days: int = 7,
) -> AdherenceSummary:
    """Computes window adherence and comparison against previous identical period."""
    today = datetime.date.today()
    end_date = today
    start_date = today - datetime.timedelta(days=window_days - 1)

    eligible, completed, current_pct = compute_adherence(db, patient_id, start_date, end_date)

    # Previous period
    prev_end = start_date - datetime.timedelta(days=1)
    prev_start = prev_end - datetime.timedelta(days=window_days - 1)
    _, _, prev_pct = compute_adherence(db, patient_id, prev_start, prev_end)

    data_status = "sufficient"
    delta = None
    trend_direction = None

    if current_pct is None:
        data_status = "no_active_goals"
    else:
        if prev_pct is not None:
            delta = round(current_pct - prev_pct, 1)
            if delta > 2.0:
                trend_direction = "improving"
            elif delta < -2.0:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_history"

    return AdherenceSummary(
        window_days=window_days,
        start_date=start_date,
        end_date=end_date,
        eligible_occurrences=eligible,
        completed_occurrences=completed,
        adherence_percentage=current_pct,
        previous_period_adherence_percentage=prev_pct,
        percentage_point_delta=delta,
        trend_direction=trend_direction,
        data_status=data_status,
    )


def compute_habit_momentum(
    db: Session,
    patient_id: int,
) -> HabitMomentumSummary:
    """
    Computes habit momentum score.
    
    Formula explicitly defined & documented:
    Momentum Score = (7-day Adherence * 0.6) + (Consecutive Logged Days Streak * 5, capped at 40)
    Scale: 0 to 100.
    - Streak Days: Consecutive days preceding/including today with at least one completed habit log.
    - Score Categories:
      >= 80: "Strong"
      60 - 79: "Steady"
      1 - 59: "Needs Attention"
      0 or Insufficient History (< 3 days logged): "Calibrating"
    """
    summary = get_adherence_summary(db, patient_id, window_days=7)
    today = datetime.date.today()

    # Calculate streak of active days
    streak = 0
    for day_offset in range(0, 30):
        check_date = today - datetime.timedelta(days=day_offset)
        has_log = (
            db.query(HabitLog)
            .filter(
                HabitLog.patient_id == patient_id,
                HabitLog.log_date == check_date,
                HabitLog.is_completed == True,
            )
            .first()
        )
        if has_log:
            streak += 1
        elif day_offset == 0:
            # If today has not been logged yet, check yesterday before breaking streak
            continue
        else:
            break

    total_logs = db.query(HabitLog).filter(HabitLog.patient_id == patient_id).count()
    if total_logs < 3 or summary.adherence_percentage is None:
        return HabitMomentumSummary(
            score=None,
            label="Calibrating",
            streak_days=streak,
            formula_documented="Weighted blend: (7-day adherence * 0.6) + min(streak * 5, 40). Requires min 3 logged days.",
        )

    score = round((summary.adherence_percentage * 0.6) + min(streak * 5.0, 40.0), 1)
    score = min(score, 100.0)

    if score >= 80:
        label = "Strong"
    elif score >= 60:
        label = "Steady"
    else:
        label = "Needs Attention"

    return HabitMomentumSummary(
        score=score,
        label=label,
        streak_days=streak,
        formula_documented="Weighted blend: (7-day adherence * 0.6) + min(streak * 5, 40). Scale: 0-100.",
    )


def get_today_goals_for_patient(
    db: Session,
    patient_id: int,
) -> DashboardGoalsSummary:
    """Retrieves all goals active for today and matches them against today's habit logs."""
    today = datetime.date.today()
    active_plan = get_active_plan_for_patient(db, patient_id)

    if not active_plan:
        return DashboardGoalsSummary(
            total=0,
            completed=0,
            remaining=0,
            completion_percentage=0.0,
            items=[],
        )

    goals = (
        db.query(WellnessGoal)
        .filter(
            WellnessGoal.plan_id == active_plan.id,
            WellnessGoal.start_date <= today,
            (WellnessGoal.end_date == None) | (WellnessGoal.end_date >= today),
        )
        .all()
    )

    items: List[GoalTodayRead] = []
    completed_count = 0

    for g in goals:
        habit = db.query(Habit).filter(Habit.id == g.habit_id).first()
        today_log = (
            db.query(HabitLog)
            .filter(
                HabitLog.patient_id == patient_id,
                HabitLog.habit_id == g.habit_id,
                HabitLog.log_date == today,
            )
            .first()
        )

        is_completed = today_log.is_completed if today_log else False
        if is_completed:
            completed_count += 1

        items.append(
            GoalTodayRead(
                goal_id=g.id,
                habit_id=g.habit_id,
                habit_code=habit.code if habit else "",
                habit_name=habit.name if habit else g.title,
                category=habit.category if habit else "activity",
                title=g.title,
                description=g.description,
                target_value=g.target_value,
                target_unit=g.target_unit,
                priority=g.priority,
                recommended_time=g.recommended_time,
                is_completed_today=is_completed,
                today_log_id=today_log.id if today_log else None,
                today_numeric_value=today_log.numeric_value if today_log else None,
                today_user_reported_barrier=today_log.user_reported_barrier if today_log else None,
            )
        )

    total = len(items)
    remaining = total - completed_count
    pct = round((completed_count / total * 100.0), 1) if total > 0 else 0.0

    return DashboardGoalsSummary(
        total=total,
        completed=completed_count,
        remaining=remaining,
        completion_percentage=pct,
        items=items,
    )


def build_dashboard_data(
    db: Session,
    patient: Patient,
) -> PatientDashboardResponse:
    """Builds unified, strongly-typed patient dashboard payload."""
    active_plan = get_active_plan_for_patient(db, patient.id)
    today_goals = get_today_goals_for_patient(db, patient.id)
    weekly_adherence_summary = get_adherence_summary(db, patient.id, window_days=7)
    momentum = compute_habit_momentum(db, patient.id)

    # Active Drift & Recovery integration (Phase 3)
    from app.services.drift_detector import run_drift_analysis
    from app.models.wellness import RecoveryProposal

    # Check for pending recovery proposal
    pending_proposal = (
        db.query(RecoveryProposal)
        .filter(RecoveryProposal.patient_id == patient.id, RecoveryProposal.status == "pending")
        .order_by(RecoveryProposal.created_at.desc())
        .first()
    )

    # Check persisted active drift event first to preserve scenario-specific baseline
    drift_orm = (
        db.query(DriftEvent)
        .filter(DriftEvent.patient_id == patient.id, DriftEvent.status == "Active")
        .first()
    )

    if drift_orm:
        try:
            drift_analysis = run_drift_analysis(db, patient.id, persist_event=False)
            contributing = drift_analysis.contributing_observations
        except Exception:
            contributing = []

        call_to_action = "Review adaptive recovery proposal to rebuild sustainable adherence."
        drift_detector = DriftDetectorSummary(
            has_drift=True,
            status="Active",
            baseline_adherence=drift_orm.baseline_adherence,
            current_adherence=drift_orm.current_adherence,
            percentage_point_change=drift_orm.percentage_point_change,
            severity="High" if drift_orm.percentage_point_change <= -25.0 else "Moderate",
            observation_window=drift_orm.observation_window,
            data_sufficiency="sufficient",
            flag_reason=drift_orm.flag_reason,
            recovery_suggestion=drift_orm.recovery_suggestion,
            contributing_observations=contributing,
            recovery_proposal_call_to_action=call_to_action,
            has_pending_recovery_proposal=pending_proposal is not None,
            pending_recovery_proposal_id=pending_proposal.id if pending_proposal else None,
            details=DriftEventRead.model_validate(drift_orm),
        )
    elif not active_plan or active_plan.status != "Active":
        drift_detector = DriftDetectorSummary(
            has_drift=False,
            status="No Active Plan",
            data_sufficiency="no_active_goals",
            flag_reason="Patient does not currently have an active wellness protocol.",
        )
    else:
        # Check if patient has sufficient logs
        logs_count = db.query(HabitLog).filter(HabitLog.patient_id == patient.id).count()
        if logs_count < 7:
            drift_detector = DriftDetectorSummary(
                has_drift=False,
                status="Unavailable - Insufficient Baseline",
                data_sufficiency="insufficient_baseline",
                flag_reason="Requires at least 7 days of recorded habit telemetry to calibrate drift baseline.",
            )
        else:
            try:
                drift_analysis = run_drift_analysis(db, patient.id, persist_event=False)
                has_drift = drift_analysis.has_drift
                status_label = "Active" if has_drift else ("Stable" if drift_analysis.status == "Improving" else drift_analysis.status)
                drift_detector = DriftDetectorSummary(
                    has_drift=has_drift,
                    status=status_label,
                    baseline_adherence=drift_analysis.baseline_adherence,
                    current_adherence=drift_analysis.recent_adherence,
                    percentage_point_change=drift_analysis.percentage_point_change,
                    severity="Normal",
                    observation_window=f"{drift_analysis.recent_start_date} to {drift_analysis.recent_end_date}" if drift_analysis.recent_start_date else None,
                    data_sufficiency=drift_analysis.data_sufficiency,
                    flag_reason=drift_analysis.explanation,
                    recovery_suggestion="Consider flexible goal targets or schedule adjustments.",
                    contributing_observations=drift_analysis.contributing_observations,
                    has_pending_recovery_proposal=pending_proposal is not None,
                    pending_recovery_proposal_id=pending_proposal.id if pending_proposal else None,
                )
            except Exception:
                drift_detector = DriftDetectorSummary(
                    has_drift=False,
                    status="Stable",
                    flag_reason="Adherence monitored against clinical baseline.",
                )

    # Recent measurements (Latest 5)
    measurements_orm = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient.id)
        .order_by(Measurement.recorded_at.desc())
        .limit(5)
        .all()
    )

    # Profile Completeness
    from app.api.routes.patients import get_patient_profile
    completeness = get_patient_profile(str(patient.id), db)

    # Plan Read schema
    plan_read = None
    if active_plan:
        goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
        plan_read = WellnessPlanRead(
            id=active_plan.id,
            patient_id=active_plan.patient_id,
            plan_name=active_plan.plan_name,
            version=active_plan.version,
            status=active_plan.status,
            description=active_plan.description,
            created_at=active_plan.created_at,
            updated_at=active_plan.updated_at,
            goals=[WellnessGoalRead.model_validate(g) for g in goals],
        )

    return PatientDashboardResponse(
        patient=PatientBase(
            synthetic_identifier=patient.synthetic_identifier,
            display_name=patient.display_name,
            age=patient.age,
            gender=patient.gender,
            primary_condition=patient.primary_condition,
            condition_severity=patient.condition_severity,
            condition_notes=patient.condition_notes,
            secondary_conditions=patient.secondary_conditions or [],
            profile_completeness=patient.profile_completeness,
            data_quality_rating=patient.data_quality_rating,
            preferences=patient.preferences or {},
            is_synthetic=patient.is_synthetic,
        ),
        patient_id=patient.id,
        active_plan=plan_read,
        plan_status=active_plan.status if active_plan else "No Active Plan",
        today_goals=today_goals,
        weekly_adherence=DashboardAdherenceSummary(
            current_week_percentage=weekly_adherence_summary.adherence_percentage,
            previous_week_percentage=weekly_adherence_summary.previous_period_adherence_percentage,
            percentage_point_delta=weekly_adherence_summary.percentage_point_delta,
            trend_direction=weekly_adherence_summary.trend_direction,
            data_status=weekly_adherence_summary.data_status,
        ),
        habit_momentum=momentum,
        recent_measurements=[MeasurementRead.model_validate(m) for m in measurements_orm],
        profile_completeness=completeness,
        drift_detector=drift_detector,
    )
