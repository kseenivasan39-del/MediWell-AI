import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    HabitLog,
    Habit,
    DriftEvent,
)
from app.schemas.wellness import (
    DriftAnalysisResponse,
    ContributingObservation,
)
from app.services.wellness_service import (
    compute_adherence,
    get_active_plan_for_patient,
)


def calculate_window_dates(
    as_of_date: datetime.date,
    recent_days: int,
    baseline_days: int,
) -> Tuple[datetime.date, datetime.date, datetime.date, datetime.date]:
    """
    Computes strict, non-overlapping date boundaries for recent and baseline observation windows.

    - Recent window: [as_of_date - (recent_days - 1), as_of_date] (length: recent_days)
    - Baseline window: [recent_start - baseline_days, recent_start - 1] (length: baseline_days)

    Guarantee: baseline_end < recent_start, strictly non-overlapping.
    """
    recent_end = as_of_date
    recent_start = recent_end - datetime.timedelta(days=recent_days - 1)
    baseline_end = recent_start - datetime.timedelta(days=1)
    baseline_start = baseline_end - datetime.timedelta(days=baseline_days - 1)
    return baseline_start, baseline_end, recent_start, recent_end


def analyze_contributing_factors(
    db: Session,
    patient_id: int,
    plan_id: int,
    recent_start: datetime.date,
    recent_end: datetime.date,
    baseline_start: datetime.date,
    baseline_end: datetime.date,
) -> List[ContributingObservation]:
    """
    Deterministic contributing factor analysis.
    Identifies:
    1. Habit-level adherence decline (comparing baseline vs recent for each prescribed habit).
    2. User-reported barriers recorded during the recent window.
    3. Time-of-day concentration patterns (e.g. evening routines missed).
    4. Incomplete logging behavior.

    Never invents diagnoses or medical causality; cites specific evidence source and date range.
    """
    observations: List[ContributingObservation] = []

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == plan_id).all()
    if not goals:
        return observations

    # 1. Habit-level adherence breakdown
    for goal in goals:
        habit = db.query(Habit).filter(Habit.id == goal.habit_id).first()
        habit_name = habit.name if habit else f"Habit #{goal.habit_id}"

        # Baseline habit completion
        b_eligible = 0
        curr = baseline_start
        while curr <= baseline_end:
            if goal.start_date <= curr and (goal.end_date is None or goal.end_date >= curr):
                b_eligible += 1
            curr += datetime.timedelta(days=1)

        b_completed = (
            db.query(HabitLog)
            .filter(
                HabitLog.patient_id == patient_id,
                HabitLog.habit_id == goal.habit_id,
                HabitLog.log_date >= baseline_start,
                HabitLog.log_date <= baseline_end,
                HabitLog.is_completed == True,
            )
            .count()
        )

        # Recent habit completion
        r_eligible = 0
        curr = recent_start
        while curr <= recent_end:
            if goal.start_date <= curr and (goal.end_date is None or goal.end_date >= curr):
                r_eligible += 1
            curr += datetime.timedelta(days=1)

        r_completed = (
            db.query(HabitLog)
            .filter(
                HabitLog.patient_id == patient_id,
                HabitLog.habit_id == goal.habit_id,
                HabitLog.log_date >= recent_start,
                HabitLog.log_date <= recent_end,
                HabitLog.is_completed == True,
            )
            .count()
        )

        b_pct = (b_completed / b_eligible * 100.0) if b_eligible > 0 else None
        r_pct = (r_completed / r_eligible * 100.0) if r_eligible > 0 else None

        if b_pct is not None and r_pct is not None:
            delta = r_pct - b_pct
            if delta <= -15.0:
                observations.append(
                    ContributingObservation(
                        category="habit_decline",
                        habit_id=goal.habit_id,
                        habit_name=habit_name,
                        observation=(
                            f"Adherence for '{habit_name}' dropped by {abs(round(delta, 1))} percentage points "
                            f"(from {round(b_pct, 1)}% baseline to {round(r_pct, 1)}% recent)."
                        ),
                        evidence_source="habit_logs",
                        date_range=f"{recent_start} to {recent_end}",
                        severity="high" if delta <= -30.0 else "moderate",
                    )
                )

                # Time pattern check
                if goal.recommended_time:
                    observations.append(
                        ContributingObservation(
                            category="timing_pattern",
                            habit_id=goal.habit_id,
                            habit_name=habit_name,
                            observation=(
                                f"Observed decline corresponds to routine scheduled for '{goal.recommended_time}'. "
                                f"Potential schedule or timing friction."
                            ),
                            evidence_source="schedule_comparison",
                            date_range=f"{recent_start} to {recent_end}",
                            severity="moderate",
                        )
                    )

    # 2. Recorded user-reported barriers
    recent_barrier_logs = (
        db.query(HabitLog)
        .filter(
            HabitLog.patient_id == patient_id,
            HabitLog.log_date >= recent_start,
            HabitLog.log_date <= recent_end,
            HabitLog.user_reported_barrier.isnot(None),
            HabitLog.user_reported_barrier != "",
        )
        .all()
    )

    barriers_seen = set()
    for blog in recent_barrier_logs:
        barrier_text = blog.user_reported_barrier.strip()
        if barrier_text and barrier_text not in barriers_seen:
            barriers_seen.add(barrier_text)
            habit = db.query(Habit).filter(Habit.id == blog.habit_id).first()
            habit_name = habit.name if habit else "prescribed habit"
            observations.append(
                ContributingObservation(
                    category="user_reported_barrier",
                    habit_id=blog.habit_id,
                    habit_name=habit_name,
                    observation=f"Patient logged barrier on {blog.log_date}: '{barrier_text}'",
                    evidence_source="user_reported_barrier",
                    date_range=str(blog.log_date),
                    barrier_reported=barrier_text,
                    severity="high",
                )
            )

    # If no recorded barriers were found despite observed drift
    if not barriers_seen:
        observations.append(
            ContributingObservation(
                category="user_reported_barrier",
                habit_id=None,
                habit_name=None,
                observation=(
                    "No explicit user barriers or friction points were recorded in habit logs during this window. "
                    "Specific reason is unconfirmed; invite patient to share context."
                ),
                evidence_source="user_reported_barrier",
                date_range=f"{recent_start} to {recent_end}",
                severity="mild",
            )
        )

    # 3. Check for incomplete logging (unlogged scheduled days)
    unlogged_count = 0
    curr = recent_start
    while curr <= recent_end:
        day_logs = (
            db.query(HabitLog)
            .filter(HabitLog.patient_id == patient_id, HabitLog.log_date == curr)
            .count()
        )
        if day_logs == 0:
            unlogged_count += 1
        curr += datetime.timedelta(days=1)

    if unlogged_count > 0:
        observations.append(
            ContributingObservation(
                category="incomplete_logging",
                habit_id=None,
                habit_name=None,
                observation=(
                    f"Telemetry gap: {unlogged_count} day(s) had zero recorded logs in the recent {recent_end - recent_start + datetime.timedelta(days=1)} window. "
                    f"Missing logs are counted as non-adherent per protocol rules."
                ),
                evidence_source="habit_logs",
                date_range=f"{recent_start} to {recent_end}",
                severity="moderate",
            )
        )

    return observations


def run_drift_analysis(
    db: Session,
    patient_id: int,
    as_of_date: Optional[datetime.date] = None,
    recent_days: Optional[int] = None,
    baseline_days: Optional[int] = None,
    threshold_percentage_points: Optional[float] = None,
    persist_event: bool = True,
) -> DriftAnalysisResponse:
    """
    Main deterministic wellness drift detection routine.

    Pure mathematical rules:
    - Recent window: recent_days ending at as_of_date.
    - Baseline window: baseline_days ending immediately prior to recent window.
    - Eligible count minimum: at least DRIFT_MIN_OCCURRENCES in both windows.
    - Drift alert trigger: (recent_adherence - baseline_adherence) <= -threshold_percentage_points (unrounded decision).
    - Idempotent event persistence: does not duplicate active drift records for the same patient, plan, and window.
    """
    if as_of_date is None:
        as_of_date = datetime.date.today()

    r_days = recent_days if recent_days is not None else settings.DRIFT_RECENT_DAYS
    b_days = baseline_days if baseline_days is not None else settings.DRIFT_BASELINE_DAYS
    threshold = (
        threshold_percentage_points
        if threshold_percentage_points is not None
        else settings.DRIFT_ALERT_THRESHOLD_PCT
    )

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError(f"Patient with id {patient_id} not found")

    active_plan = get_active_plan_for_patient(db, patient_id)
    if not active_plan:
        return DriftAnalysisResponse(
            patient_id=patient.id,
            synthetic_identifier=patient.synthetic_identifier,
            plan_id=None,
            has_drift=False,
            status="no_active_plan",
            data_sufficiency="no_active_goals",
            threshold_percentage_points=threshold,
            explanation="Patient does not currently have an active wellness plan. Drift analysis requires an active protocol.",
        )

    b_start, b_end, r_start, r_end = calculate_window_dates(as_of_date, r_days, b_days)

    # Calculate baseline adherence
    b_eligible, b_completed, b_pct = compute_adherence(db, patient_id, b_start, b_end)
    # Calculate recent adherence
    r_eligible, r_completed, r_pct = compute_adherence(db, patient_id, r_start, r_end)

    min_occ = settings.DRIFT_MIN_OCCURRENCES

    # Evaluate data sufficiency
    if b_eligible < min_occ:
        return DriftAnalysisResponse(
            patient_id=patient.id,
            synthetic_identifier=patient.synthetic_identifier,
            plan_id=active_plan.id,
            has_drift=False,
            status="insufficient_data",
            data_sufficiency="insufficient_baseline",
            baseline_start_date=b_start,
            baseline_end_date=b_end,
            recent_start_date=r_start,
            recent_end_date=r_end,
            baseline_eligible=b_eligible,
            baseline_completed=b_completed,
            recent_eligible=r_eligible,
            recent_completed=r_completed,
            baseline_adherence=b_pct,
            recent_adherence=r_pct,
            threshold_percentage_points=threshold,
            explanation=(
                f"Insufficient historical baseline telemetry ({b_eligible} eligible scheduled occurrences; "
                f"minimum required: {min_occ}). Calibration pending."
            ),
        )

    if r_eligible < min_occ:
        return DriftAnalysisResponse(
            patient_id=patient.id,
            synthetic_identifier=patient.synthetic_identifier,
            plan_id=active_plan.id,
            has_drift=False,
            status="insufficient_data",
            data_sufficiency="insufficient_recent",
            baseline_start_date=b_start,
            baseline_end_date=b_end,
            recent_start_date=r_start,
            recent_end_date=r_end,
            baseline_eligible=b_eligible,
            baseline_completed=b_completed,
            recent_eligible=r_eligible,
            recent_completed=r_completed,
            baseline_adherence=b_pct,
            recent_adherence=r_pct,
            threshold_percentage_points=threshold,
            explanation=(
                f"Insufficient recent scheduled occurrences ({r_eligible} eligible occurrences; "
                f"minimum required: {min_occ})."
            ),
        )

    # Both windows have sufficient data
    # Calculate exact unrounded differences
    raw_b_rate = (b_completed / b_eligible) * 100.0
    raw_r_rate = (r_completed / r_eligible) * 100.0
    raw_delta = raw_r_rate - raw_b_rate

    # Relative percentage change: (recent - baseline) / baseline * 100
    relative_change = None
    if raw_b_rate > 0:
        relative_change = round(((raw_r_rate - raw_b_rate) / raw_b_rate) * 100.0, 1)

    # Unrounded threshold decision
    is_drift = raw_delta <= -threshold

    if is_drift:
        status = "Active"
    elif raw_delta >= threshold:
        status = "Improving"
    else:
        status = "Stable"

    # Analyze contributing observations
    observations = analyze_contributing_factors(
        db, patient_id, active_plan.id, r_start, r_end, b_start, b_end
    )

    if is_drift:
        explanation = (
            f"Adherence declined by {abs(round(raw_delta, 1))} percentage points below the established baseline "
            f"({round(raw_b_rate, 1)}% baseline vs {round(raw_r_rate, 1)}% recent). "
            f"Exceeds configured alert threshold of {threshold} percentage points."
        )
    elif status == "Improving":
        explanation = (
            f"Adherence improved by {round(raw_delta, 1)} percentage points over baseline "
            f"({round(raw_b_rate, 1)}% baseline to {round(raw_r_rate, 1)}% recent)."
        )
    else:
        explanation = (
            f"Adherence is stable within normal variation. Recent adherence is {round(raw_r_rate, 1)}% "
            f"compared to baseline {round(raw_b_rate, 1)}% (delta: {round(raw_delta, 1)} pp)."
        )

    drift_event_id = None
    if is_drift and persist_event:
        obs_window_label = f"{r_days}d vs {b_days}d baseline ({r_start} to {r_end})"

        # Check existing active drift event for idempotency
        existing_event = (
            db.query(DriftEvent)
            .filter(
                DriftEvent.patient_id == patient_id,
                DriftEvent.plan_id == active_plan.id,
                DriftEvent.recent_start_date == r_start,
                DriftEvent.recent_end_date == r_end,
                DriftEvent.status == "Active",
            )
            .first()
        )

        if existing_event:
            # Update existing event with latest run
            existing_event.baseline_adherence = round(raw_b_rate, 1)
            existing_event.current_adherence = round(raw_r_rate, 1)
            existing_event.percentage_point_change = round(raw_delta, 1)
            existing_event.relative_change_pct = relative_change
            existing_event.flag_reason = explanation
            existing_event.contributing_factors = [o.model_dump() for o in observations]
            db.commit()
            db.refresh(existing_event)
            drift_event_id = existing_event.id
        else:
            new_event = DriftEvent(
                patient_id=patient_id,
                plan_id=active_plan.id,
                baseline_adherence=round(raw_b_rate, 1),
                current_adherence=round(raw_r_rate, 1),
                percentage_point_change=round(raw_delta, 1),
                relative_change_pct=relative_change,
                observation_window=obs_window_label,
                baseline_start_date=b_start,
                baseline_end_date=b_end,
                recent_start_date=r_start,
                recent_end_date=r_end,
                baseline_eligible=b_eligible,
                baseline_completed=b_completed,
                recent_eligible=r_eligible,
                recent_completed=r_completed,
                status="Active",
                flag_reason=explanation,
                recovery_suggestion="Review personalized recovery proposal with flexible targets or schedule adjustments.",
                contributing_factors=[o.model_dump() for o in observations],
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            drift_event_id = new_event.id

    return DriftAnalysisResponse(
        patient_id=patient.id,
        synthetic_identifier=patient.synthetic_identifier,
        plan_id=active_plan.id,
        has_drift=is_drift,
        status=status,
        data_sufficiency="sufficient",
        baseline_start_date=b_start,
        baseline_end_date=b_end,
        recent_start_date=r_start,
        recent_end_date=r_end,
        baseline_eligible=b_eligible,
        baseline_completed=b_completed,
        recent_eligible=r_eligible,
        recent_completed=r_completed,
        baseline_adherence=round(raw_b_rate, 1),
        recent_adherence=round(raw_r_rate, 1),
        percentage_point_change=round(raw_delta, 1),
        relative_change_pct=relative_change,
        threshold_percentage_points=threshold,
        explanation=explanation,
        contributing_observations=observations,
        drift_event_id=drift_event_id,
    )
