import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    synthetic_identifier = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(32), nullable=False)

    # Condition context & clinical categories
    primary_condition = Column(String(128), nullable=False)
    condition_severity = Column(String(64), nullable=False, default="Under Review")
    condition_notes = Column(Text, nullable=True)

    # Secondary conditions stored as structured JSON list
    secondary_conditions = Column(JSON, nullable=False, default=list)

    # Profile attributes, telemetry status & completeness
    profile_completeness = Column(Integer, nullable=False, default=0) # percentage 0-100
    data_quality_rating = Column(String(64), nullable=False, default="Sparse")
    preferences = Column(JSON, nullable=False, default=dict)
    is_synthetic = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    wellness_plans = relationship("WellnessPlan", back_populates="patient", cascade="all, delete-orphan")
    habit_logs = relationship("HabitLog", back_populates="patient", cascade="all, delete-orphan")
    measurements = relationship("Measurement", back_populates="patient", cascade="all, delete-orphan")
    drift_events = relationship("DriftEvent", back_populates="patient", cascade="all, delete-orphan")
    recovery_proposals = relationship("RecoveryProposal", back_populates="patient", cascade="all, delete-orphan")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True) # e.g. "morning_walk"
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False, index=True) # nutrition, hydration, activity, sleep, etc.
    description = Column(Text, nullable=True)
    default_unit = Column(String(32), nullable=True) # min, ml, steps, hours, mg
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    goals = relationship("WellnessGoal", back_populates="habit")
    habit_logs = relationship("HabitLog", back_populates="habit")


class WellnessPlan(Base):
    __tablename__ = "wellness_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False, default="v1.0")
    status = Column(String(32), nullable=False, default="Active") # Active, Under Review, Completed, Paused
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    patient = relationship("Patient", back_populates="wellness_plans")
    goals = relationship("WellnessGoal", back_populates="plan", cascade="all, delete-orphan")


class WellnessGoal(Base):
    __tablename__ = "wellness_goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("wellness_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=True)
    target_unit = Column(String(32), nullable=True)
    frequency = Column(String(32), nullable=False, default="daily") # daily, 3x_week, weekly
    recommended_time = Column(String(32), nullable=True)
    priority = Column(String(16), nullable=False, default="medium") # high, medium, low
    is_completed_today = Column(Boolean, nullable=False, default=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Relationships
    plan = relationship("WellnessPlan", back_populates="goals")
    habit = relationship("Habit", back_populates="goals")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    log_date = Column(Date, nullable=False, index=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    numeric_value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    user_reported_barrier = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    patient = relationship("Patient", back_populates="habit_logs")
    habit = relationship("Habit", back_populates="habit_logs")

    __table_args__ = (
        UniqueConstraint("patient_id", "habit_id", "log_date", name="uq_patient_habit_log_date"),
        Index("idx_patient_habit_date", "patient_id", "habit_id", "log_date"),
    )


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    measurement_type = Column(String(64), nullable=False, index=True) # e.g. blood_glucose, systolic_bp, weight, hba1c
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    context_notes = Column(String(256), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="measurements")


class DriftEvent(Base):
    __tablename__ = "drift_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("wellness_plans.id", ondelete="SET NULL"), nullable=True, index=True)
    baseline_adherence = Column(Float, nullable=False) # e.g. 86.0 (%)
    current_adherence = Column(Float, nullable=False) # e.g. 62.0 (%)
    percentage_point_change = Column(Float, nullable=False) # e.g. -24.0
    relative_change_pct = Column(Float, nullable=True) # e.g. -27.9 (%)
    observation_window = Column(String(64), nullable=False) # e.g. "Past 7 days vs baseline"
    baseline_start_date = Column(Date, nullable=True)
    baseline_end_date = Column(Date, nullable=True)
    recent_start_date = Column(Date, nullable=True)
    recent_end_date = Column(Date, nullable=True)
    baseline_eligible = Column(Integer, nullable=True)
    baseline_completed = Column(Integer, nullable=True)
    recent_eligible = Column(Integer, nullable=True)
    recent_completed = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="Active") # Active, Acknowledged, Resolved
    flag_reason = Column(Text, nullable=True)
    recovery_suggestion = Column(Text, nullable=True)
    contributing_factors = Column(JSON, nullable=True, default=list)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="drift_events")
    plan = relationship("WellnessPlan")


class RecoveryProposal(Base):
    __tablename__ = "recovery_proposals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("wellness_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    drift_event_id = Column(Integer, ForeignKey("drift_events.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(128), nullable=False)
    rationale = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending") # pending, accepted, edited, rejected
    decision_notes = Column(Text, nullable=True)

    # Proposed adjustments stored as structured JSON
    # List of items: { "goal_id": int, "habit_id": int, "habit_name": str, "current_target": float, "proposed_target": float, "unit": str, "recommended_time": str, "adjustment_type": str }
    proposed_adjustments = Column(JSON, nullable=False, default=list)
    user_revised_targets = Column(JSON, nullable=True) # Populated if decision == "edited"

    barrier_question = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="recovery_proposals")
    plan = relationship("WellnessPlan")
    drift_event = relationship("DriftEvent")


class CalendarIntegration(Base):
    """
    Persists the single authorized Google Calendar demo account connection.
    Access and refresh tokens are protected and encrypted at rest.
    """
    __tablename__ = "calendar_integrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(32), nullable=False, default="google")
    account_email = Column(String(256), nullable=True)
    calendar_id = Column(String(128), nullable=False, default="primary")
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scope = Column(String(256), nullable=True)
    is_connected = Column(Boolean, nullable=False, default=False)
    connected_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(64), nullable=True) # "success", "error", "partial"
    last_sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class CalendarEventMapping(Base):
    """
    Maps a synthetic patient's scheduled wellness goal to a real Google Calendar reminder event.
    Enables duplicate prevention, updates, and synchronization.
    """
    __tablename__ = "calendar_event_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("wellness_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    google_event_id = Column(String(256), nullable=False, index=True)
    calendar_id = Column(String(128), nullable=False, default="primary")
    event_title = Column(String(256), nullable=False)
    scheduled_time = Column(String(64), nullable=False) # e.g. "08:30 AM" or "08:30"
    timezone = Column(String(64), nullable=False, default="Asia/Kolkata")
    sync_status = Column(String(32), nullable=False, default="synced") # "synced", "pending", "failed"
    last_synced_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("goal_id", "calendar_id", name="uq_goal_calendar_mapping"),
    )

