from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.wellness import WellnessPlan, WellnessGoal
from app.schemas.wellness import WellnessPlanRead, WellnessGoalRead
from app.services.wellness_service import get_patient_or_404, get_active_plan_for_patient

router = APIRouter(tags=["Wellness Plans"])


@router.get(
    "/patients/{patient_id}/plans",
    response_model=List[WellnessPlanRead],
    summary="List all wellness plans for a patient",
)
def list_patient_plans(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve all wellness plans associated with a synthetic patient."""
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    plans = (
        db.query(WellnessPlan)
        .filter(WellnessPlan.patient_id == patient.id)
        .order_by(WellnessPlan.created_at.desc())
        .all()
    )

    result = []
    for p in plans:
        goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == p.id).all()
        plan_read = WellnessPlanRead(
            id=p.id,
            patient_id=p.patient_id,
            plan_name=p.plan_name,
            version=p.version,
            status=p.status,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            goals=[WellnessGoalRead.model_validate(g) for g in goals],
        )
        result.append(plan_read)

    return result


@router.get(
    "/patients/{patient_id}/plans/active",
    response_model=WellnessPlanRead,
    summary="Retrieve active wellness plan for a patient",
)
def get_patient_active_plan(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve the currently active wellness plan and goals for a synthetic patient."""
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    plan = get_active_plan_for_patient(db, patient.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active wellness plan found for patient '{patient_id}'.",
        )

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == plan.id).all()
    return WellnessPlanRead(
        id=plan.id,
        patient_id=plan.patient_id,
        plan_name=plan.plan_name,
        version=plan.version,
        status=plan.status,
        description=plan.description,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        goals=[WellnessGoalRead.model_validate(g) for g in goals],
    )


@router.get(
    "/plans/{plan_id}",
    response_model=WellnessPlanRead,
    summary="Retrieve one wellness plan by plan ID",
)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific wellness plan by its primary key ID."""
    plan = db.query(WellnessPlan).filter(WellnessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wellness plan '{plan_id}' not found.",
        )

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == plan.id).all()
    return WellnessPlanRead(
        id=plan.id,
        patient_id=plan.patient_id,
        plan_name=plan.plan_name,
        version=plan.version,
        status=plan.status,
        description=plan.description,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        goals=[WellnessGoalRead.model_validate(g) for g in goals],
    )


@router.get(
    "/plans/{plan_id}/goals",
    response_model=List[WellnessGoalRead],
    summary="Retrieve all goals configured for a wellness plan",
)
def get_plan_goals(plan_id: int, db: Session = Depends(get_db)):
    """Retrieve all specific goals belonging to a wellness plan."""
    plan = db.query(WellnessPlan).filter(WellnessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wellness plan '{plan_id}' not found.",
        )

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == plan.id).all()
    return [WellnessGoalRead.model_validate(g) for g in goals]
