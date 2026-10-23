from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    DriftEvent,
    Measurement,
    HabitLog,
)
from app.schemas.wellness import (
    PatientListItem,
    PatientDetail,
    PatientProfileCompleteness,
    PatientDashboardResponse,
    WellnessPlanRead,
    WellnessGoalRead,
    DriftEventRead,
    MeasurementRead,
)
from app.services.wellness_service import get_patient_or_404, build_dashboard_data

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "/{patient_id}/dashboard",
    response_model=PatientDashboardResponse,
    summary="Unified patient wellness dashboard",
)
def get_patient_dashboard(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieve unified, strongly-typed patient dashboard payload.
    
    Includes:
    - Synthetic identity, documented condition, and profile context.
    - Active wellness plan and protocol status.
    - Today's goals, completion states, and progress percentage.
    - Weekly adherence rate and comparison against previous period.
    - Habit momentum score with explicitly documented formula.
    - Latest biomarker measurements.
    - Profile completeness and data quality ratings.
    - Wellness Drift Detector status (Active, Stable, or Insufficient Baseline).
    """
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found in synthetic database.",
        )

    return build_dashboard_data(db, patient)


@router.get("", response_model=List[PatientListItem], summary="List synthetic demo patients")
def list_patients(db: Session = Depends(get_db)):
    """Retrieve all synthetic demo patients with summary indicators."""
    patients = db.query(Patient).order_by(Patient.id).all()
    
    result = []
    for p in patients:
        active_plan = (
            db.query(WellnessPlan)
            .filter(WellnessPlan.patient_id == p.id, WellnessPlan.status == "Active")
            .first()
        )
        active_drift = (
            db.query(DriftEvent)
            .filter(DriftEvent.patient_id == p.id, DriftEvent.status == "Active")
            .first()
        )
        
        result.append(
            PatientListItem(
                id=p.id,
                synthetic_identifier=p.synthetic_identifier,
                display_name=p.display_name,
                age=p.age,
                gender=p.gender,
                primary_condition=p.primary_condition,
                condition_severity=p.condition_severity,
                profile_completeness=p.profile_completeness,
                data_quality_rating=p.data_quality_rating,
                active_plan_name=active_plan.plan_name if active_plan else None,
                has_active_drift=active_drift is not None,
                is_synthetic=p.is_synthetic,
            )
        )
    return result


@router.get("/{patient_id}", response_model=PatientDetail, summary="Retrieve one patient by ID or synthetic identifier")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full details for one patient.
    Supports either integer database ID (e.g. 1) or synthetic identifier (e.g. SYNTH-T2D-8841).
    """
    query = db.query(Patient)
    if patient_id.isdigit():
        patient = query.filter(Patient.id == int(patient_id)).first()
    else:
        patient = query.filter(Patient.synthetic_identifier == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found in synthetic database.",
        )

    # Active plan with goals
    active_plan_orm = (
        db.query(WellnessPlan)
        .filter(WellnessPlan.patient_id == patient.id, WellnessPlan.status == "Active")
        .first()
    )
    active_plan = None
    if active_plan_orm:
        goals = (
            db.query(WellnessGoal)
            .filter(WellnessGoal.plan_id == active_plan_orm.id)
            .all()
        )
        active_plan = WellnessPlanRead(
            id=active_plan_orm.id,
            plan_name=active_plan_orm.plan_name,
            version=active_plan_orm.version,
            status=active_plan_orm.status,
            description=active_plan_orm.description,
            goals=[WellnessGoalRead.model_validate(g) for g in goals],
        )

    # Active drift event
    drift_orm = (
        db.query(DriftEvent)
        .filter(DriftEvent.patient_id == patient.id, DriftEvent.status == "Active")
        .first()
    )
    active_drift = DriftEventRead.model_validate(drift_orm) if drift_orm else None

    # Recent measurements (latest 5)
    measurements_orm = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient.id)
        .order_by(Measurement.recorded_at.desc())
        .limit(5)
        .all()
    )
    recent_measurements = [MeasurementRead.model_validate(m) for m in measurements_orm]

    return PatientDetail(
        id=patient.id,
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
        created_at=patient.created_at,
        active_plan=active_plan,
        active_drift=active_drift,
        recent_measurements=recent_measurements,
    )


@router.get("/{patient_id}/profile", response_model=PatientProfileCompleteness, summary="Retrieve patient profile completeness and data quality")
def get_patient_profile(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve profile completeness analysis, telemetry history status, and checklist."""
    query = db.query(Patient)
    if patient_id.isdigit():
        patient = query.filter(Patient.id == int(patient_id)).first()
    else:
        patient = query.filter(Patient.synthetic_identifier == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found in synthetic database.",
        )

    # Compute metrics
    active_plan = (
        db.query(WellnessPlan)
        .filter(WellnessPlan.patient_id == patient.id, WellnessPlan.status == "Active")
        .first()
    )
    goals_count = 0
    if active_plan:
        goals_count = (
            db.query(WellnessGoal)
            .filter(WellnessGoal.plan_id == active_plan.id)
            .count()
        )

    # Distinct logged dates
    logged_dates_count = (
        db.query(HabitLog.log_date)
        .filter(HabitLog.patient_id == patient.id)
        .distinct()
        .count()
    )

    has_condition_context = bool(patient.primary_condition and patient.condition_notes)
    has_active_plan = active_plan is not None
    has_sufficient_history = logged_dates_count >= 7

    missing_fields = []
    if not patient.preferences:
        missing_fields.append("lifestyle_preferences")
    if not patient.secondary_conditions:
        missing_fields.append("secondary_conditions_screening")
    if logged_dates_count < 7:
        missing_fields.append("7_day_baseline_habit_telemetry")

    breakdown = {
        "demographics_and_identity": 25,
        "clinical_condition_context": 25 if has_condition_context else 10,
        "active_wellness_protocol": 25 if has_active_plan else 0,
        "habit_telemetry_history": 25 if has_sufficient_history else min(logged_dates_count * 3, 15),
    }

    return PatientProfileCompleteness(
        patient_id=patient.id,
        synthetic_identifier=patient.synthetic_identifier,
        display_name=patient.display_name,
        profile_completeness=patient.profile_completeness,
        data_quality_rating=patient.data_quality_rating,
        has_condition_context=has_condition_context,
        has_active_plan=has_active_plan,
        total_goals_configured=goals_count,
        total_logged_days=logged_dates_count,
        has_sufficient_history=has_sufficient_history,
        missing_fields=missing_fields,
        completeness_breakdown=breakdown,
    )
