import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from app.models.wellness import Habit, HabitLog, WellnessGoal, WellnessPlan
from app.schemas.wellness import (
    HabitRead,
    HabitLogCreate,
    HabitLogUpdate,
    HabitLogRead,
    PaginatedHabitLogs,
    GoalTodayRead,
)
from app.services.wellness_service import (
    get_patient_or_404,
    get_active_plan_for_patient,
    get_today_goals_for_patient,
)

router = APIRouter(tags=["Habits & Daily Goals"])


@router.get(
    "/patients/{patient_id}/habits",
    response_model=List[HabitRead],
    summary="List available habits for a patient or master habit catalog",
)
def list_patient_habits(
    patient_id: str,
    active_only: bool = Query(True, description="Filter for active habits only"),
    db: Session = Depends(get_db),
):
    """Retrieve habits configured in patient's plan, or all active system habits."""
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    # Return habits linked to patient's active plan, or fallback to all active habits
    active_plan = get_active_plan_for_patient(db, patient.id)
    if active_plan:
        goal_habit_ids = [
            g.habit_id
            for g in db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
        ]
        habits = db.query(Habit).filter(Habit.id.in_(goal_habit_ids)).all()
    else:
        query = db.query(Habit)
        if active_only:
            query = query.filter(Habit.is_active == True)
        habits = query.all()

    return [HabitRead.model_validate(h) for h in habits]


@router.get(
    "/patients/{patient_id}/goals/today",
    response_model=List[GoalTodayRead],
    summary="List daily goals scheduled for today with real-time completion status",
)
def list_today_goals(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieve today's scheduled goals for the patient.
    Status is determined by matching against logged habit records for today's date.
    """
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    goals_summary = get_today_goals_for_patient(db, patient.id)
    return goals_summary.items


@router.get(
    "/patients/{patient_id}/habits/logs",
    response_model=PaginatedHabitLogs,
    summary="Retrieve habit logs with optional date range and pagination",
)
def list_habit_logs(
    patient_id: str,
    start_date: Optional[datetime.date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    habit_id: Optional[int] = Query(None, description="Filter for specific habit ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve historical habit logs with date filtering and pagination."""
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    query = db.query(HabitLog).filter(HabitLog.patient_id == patient.id)

    if start_date:
        query = query.filter(HabitLog.log_date >= start_date)
    if end_date:
        query = query.filter(HabitLog.log_date <= end_date)
    if habit_id:
        query = query.filter(HabitLog.habit_id == habit_id)

    total = query.count()
    logs = (
        query.order_by(HabitLog.log_date.desc(), HabitLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for l in logs:
        habit = db.query(Habit).filter(Habit.id == l.habit_id).first()
        items.append(
            HabitLogRead(
                id=l.id,
                patient_id=l.patient_id,
                habit_id=l.habit_id,
                habit_name=habit.name if habit else None,
                habit_code=habit.code if habit else None,
                category=habit.category if habit else None,
                log_date=l.log_date,
                is_completed=l.is_completed,
                numeric_value=l.numeric_value,
                unit=l.unit,
                user_reported_barrier=l.user_reported_barrier,
                notes=l.notes,
                created_at=l.created_at,
                updated_at=l.updated_at,
            )
        )

    return PaginatedHabitLogs(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.post(
    "/patients/{patient_id}/habits/logs",
    response_model=HabitLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new habit log entry",
)
def create_habit_log(
    patient_id: str,
    payload: HabitLogCreate,
    db: Session = Depends(get_db),
):
    """
    Record a habit log entry.
    
    Validation & Integrity:
    - Validates patient existence.
    - Validates habit existence and ownership in patient's plan/master catalog.
    - Validates date cannot be in the future.
    - Checks for duplicate log on the same (patient, habit, date) and raises 409 Conflict.
    - Supports user-reported barriers (e.g. fatigue, time conflict).
    """
    patient = get_patient_or_404(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )

    habit = db.query(Habit).filter(Habit.id == payload.habit_id).first()
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with ID '{payload.habit_id}' does not exist.",
        )

    today = datetime.date.today()
    if payload.log_date > today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot record habit completion logs for future dates.",
        )

    # Unit validation if numeric value is supplied
    if payload.numeric_value is not None and payload.numeric_value < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Habit numeric value cannot be negative.",
        )

    # Check for existing log on this date
    existing = (
        db.query(HabitLog)
        .filter(
            HabitLog.patient_id == patient.id,
            HabitLog.habit_id == payload.habit_id,
            HabitLog.log_date == payload.log_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A habit log already exists for habit ID {payload.habit_id} on {payload.log_date}. "
                f"Use PATCH /api/v1/habit-logs/{existing.id} to update or correct this entry."
            ),
        )

    log_entry = HabitLog(
        patient_id=patient.id,
        habit_id=payload.habit_id,
        log_date=payload.log_date,
        is_completed=payload.is_completed,
        numeric_value=payload.numeric_value,
        unit=payload.unit or habit.default_unit,
        user_reported_barrier=payload.user_reported_barrier,
        notes=payload.notes,
    )

    try:
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate entry violation. Record already exists for this habit and date.",
        )

    return HabitLogRead(
        id=log_entry.id,
        patient_id=log_entry.patient_id,
        habit_id=log_entry.habit_id,
        habit_name=habit.name,
        habit_code=habit.code,
        category=habit.category,
        log_date=log_entry.log_date,
        is_completed=log_entry.is_completed,
        numeric_value=log_entry.numeric_value,
        unit=log_entry.unit,
        user_reported_barrier=log_entry.user_reported_barrier,
        notes=log_entry.notes,
        created_at=log_entry.created_at,
        updated_at=log_entry.updated_at,
    )


@router.patch(
    "/habit-logs/{log_id}",
    response_model=HabitLogRead,
    summary="Update or correct an existing habit log",
)
def update_habit_log(
    log_id: int,
    payload: HabitLogUpdate,
    db: Session = Depends(get_db),
):
    """
    Auditable in-place update of an existing habit log.
    Updates completion status, numeric values, or user-reported barriers.
    Maintains updated_at timestamp.
    """
    log_entry = db.query(HabitLog).filter(HabitLog.id == log_id).first()
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit log '{log_id}' not found.",
        )

    habit = db.query(Habit).filter(Habit.id == log_entry.habit_id).first()

    update_data = payload.model_dump(exclude_unset=True)
    if "numeric_value" in update_data and update_data["numeric_value"] is not None:
        if update_data["numeric_value"] < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Habit numeric value cannot be negative.",
            )

    for field, val in update_data.items():
        setattr(log_entry, field, val)

    log_entry.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(log_entry)

    return HabitLogRead(
        id=log_entry.id,
        patient_id=log_entry.patient_id,
        habit_id=log_entry.habit_id,
        habit_name=habit.name if habit else None,
        habit_code=habit.code if habit else None,
        category=habit.category if habit else None,
        log_date=log_entry.log_date,
        is_completed=log_entry.is_completed,
        numeric_value=log_entry.numeric_value,
        unit=log_entry.unit,
        user_reported_barrier=log_entry.user_reported_barrier,
        notes=log_entry.notes,
        created_at=log_entry.created_at,
        updated_at=log_entry.updated_at,
    )
