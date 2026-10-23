from datetime import date, datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# Health Check
class HealthCheckResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str
    database: str
    synthetic_mode: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Habit Schemas
class HabitBase(BaseModel):
    code: str
    name: str
    category: str
    description: Optional[str] = None
    default_unit: Optional[str] = None
    is_active: bool = True


class HabitRead(HabitBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Wellness Goal Schemas
class WellnessGoalRead(BaseModel):
    id: int
    habit_id: int
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    frequency: str
    recommended_time: Optional[str] = None
    priority: str
    is_completed_today: bool
    start_date: date
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class GoalTodayRead(BaseModel):
    goal_id: int
    habit_id: int
    habit_code: str
    habit_name: str
    category: str
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    priority: str
    recommended_time: Optional[str] = None
    is_completed_today: bool
    today_log_id: Optional[int] = None
    today_numeric_value: Optional[float] = None
    today_user_reported_barrier: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Habit Log Schemas
class HabitLogCreate(BaseModel):
    habit_id: int
    log_date: date
    is_completed: bool
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    user_reported_barrier: Optional[str] = None
    notes: Optional[str] = None


class HabitLogUpdate(BaseModel):
    is_completed: Optional[bool] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    user_reported_barrier: Optional[str] = None
    notes: Optional[str] = None


class HabitLogRead(BaseModel):
    id: int
    patient_id: int
    habit_id: int
    habit_name: Optional[str] = None
    habit_code: Optional[str] = None
    category: Optional[str] = None
    log_date: date
    is_completed: bool
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    user_reported_barrier: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedHabitLogs(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[HabitLogRead]


# Wellness Plan Schemas
class WellnessPlanRead(BaseModel):
    id: int
    patient_id: Optional[int] = None
    plan_name: str
    version: str
    status: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    goals: List[WellnessGoalRead] = []

    model_config = ConfigDict(from_attributes=True)


# Drift Event Schemas
class DriftEventRead(BaseModel):
    id: int
    patient_id: Optional[int] = None
    plan_id: Optional[int] = None
    baseline_adherence: float
    current_adherence: float
    percentage_point_change: float
    relative_change_pct: Optional[float] = None
    observation_window: str
    baseline_start_date: Optional[date] = None
    baseline_end_date: Optional[date] = None
    recent_start_date: Optional[date] = None
    recent_end_date: Optional[date] = None
    baseline_eligible: Optional[int] = None
    baseline_completed: Optional[int] = None
    recent_eligible: Optional[int] = None
    recent_completed: Optional[int] = None
    status: str
    flag_reason: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    contributing_factors: Optional[List[Dict[str, Any]]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Contributing Factor & Analysis Schemas
class ContributingObservation(BaseModel):
    category: str # "habit_decline", "user_reported_barrier", "timing_pattern", "incomplete_logging"
    habit_id: Optional[int] = None
    habit_name: Optional[str] = None
    observation: str
    evidence_source: str # e.g. "habit_logs", "user_reported_barrier", "schedule_comparison"
    date_range: str
    barrier_reported: Optional[str] = None
    severity: str = "moderate" # "mild", "moderate", "high"


class DriftAnalysisResponse(BaseModel):
    patient_id: int
    synthetic_identifier: str
    plan_id: Optional[int] = None
    has_drift: bool
    status: str # "Active", "Stable", "Improving", "insufficient_data", "no_active_plan"
    data_sufficiency: str # "sufficient", "insufficient_baseline", "insufficient_recent", "no_active_goals"
    baseline_start_date: Optional[date] = None
    baseline_end_date: Optional[date] = None
    recent_start_date: Optional[date] = None
    recent_end_date: Optional[date] = None
    baseline_eligible: int = 0
    baseline_completed: int = 0
    recent_eligible: int = 0
    recent_completed: int = 0
    baseline_adherence: Optional[float] = None
    recent_adherence: Optional[float] = None
    percentage_point_change: Optional[float] = None
    relative_change_pct: Optional[float] = None
    threshold_percentage_points: float
    explanation: str
    contributing_observations: List[ContributingObservation] = []
    drift_event_id: Optional[int] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class DriftAnalyzeRequest(BaseModel):
    recent_days: Optional[int] = None
    baseline_days: Optional[int] = None
    threshold_percentage_points: Optional[float] = None
    persist_event: bool = True


# Recovery Proposal Schemas
class ProposedAdjustmentItem(BaseModel):
    goal_id: int
    habit_id: int
    habit_name: str
    current_target: Optional[float] = None
    proposed_target: Optional[float] = None
    unit: Optional[str] = None
    current_frequency: Optional[str] = None
    proposed_frequency: Optional[str] = None
    recommended_time: Optional[str] = None
    adjustment_type: str # "reduce_target", "adjust_schedule", "flexible_window", "temporary_pause"


class UserRevisedTargetItem(BaseModel):
    goal_id: int
    revised_target: Optional[float] = None
    revised_frequency: Optional[str] = None
    notes: Optional[str] = None


class RecoveryProposalCreate(BaseModel):
    drift_event_id: Optional[int] = None
    custom_notes: Optional[str] = None


class RecoveryProposalDecision(BaseModel):
    decision: str # "accepted", "edited", "rejected"
    decision_notes: Optional[str] = None
    user_revised_targets: Optional[List[UserRevisedTargetItem]] = None


class RecoveryProposalRead(BaseModel):
    id: int
    patient_id: int
    plan_id: int
    drift_event_id: Optional[int] = None
    title: str
    rationale: str
    status: str # "pending", "accepted", "edited", "rejected"
    decision_notes: Optional[str] = None
    proposed_adjustments: List[ProposedAdjustmentItem] = []
    user_revised_targets: Optional[List[UserRevisedTargetItem]] = None
    barrier_question: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Measurement Schemas
class MeasurementRead(BaseModel):
    id: int
    measurement_type: str
    value: float
    unit: str
    recorded_at: datetime
    context_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Patient Schemas
class PatientBase(BaseModel):
    synthetic_identifier: str
    display_name: str
    age: int
    gender: str
    primary_condition: str
    condition_severity: str
    condition_notes: Optional[str] = None
    secondary_conditions: List[Dict[str, Any]] = []
    profile_completeness: int
    data_quality_rating: str
    preferences: Dict[str, Any] = {}
    is_synthetic: bool = True


class PatientListItem(BaseModel):
    id: int
    synthetic_identifier: str
    display_name: str
    age: int
    gender: str
    primary_condition: str
    condition_severity: str
    profile_completeness: int
    data_quality_rating: str
    active_plan_name: Optional[str] = None
    has_active_drift: bool = False
    is_synthetic: bool = True

    model_config = ConfigDict(from_attributes=True)


class PatientDetail(PatientBase):
    id: int
    created_at: datetime
    active_plan: Optional[WellnessPlanRead] = None
    active_drift: Optional[DriftEventRead] = None
    recent_measurements: List[MeasurementRead] = []

    model_config = ConfigDict(from_attributes=True)


class PatientProfileCompleteness(BaseModel):
    patient_id: int
    synthetic_identifier: str
    display_name: str
    profile_completeness: int
    data_quality_rating: str
    has_condition_context: bool
    has_active_plan: bool
    total_goals_configured: int
    total_logged_days: int
    has_sufficient_history: bool
    missing_fields: List[str] = []
    completeness_breakdown: Dict[str, int] = {}


# Analytics Schemas
class AdherenceSummary(BaseModel):
    window_days: int
    start_date: date
    end_date: date
    eligible_occurrences: int
    completed_occurrences: int
    adherence_percentage: Optional[float] = None # None if insufficient data / zero occurrences
    previous_period_adherence_percentage: Optional[float] = None
    percentage_point_delta: Optional[float] = None
    trend_direction: Optional[str] = None # "improving", "declining", "stable", "insufficient_data"
    data_status: str # "sufficient", "insufficient_history", "no_active_goals"


class TrendPoint(BaseModel):
    date: date
    scheduled_goals: int
    completed_goals: int
    adherence_rate: Optional[float] = None
    category_breakdown: Dict[str, Optional[float]] = {}


class TrendsResponse(BaseModel):
    patient_id: int
    synthetic_identifier: str
    window_days: int
    start_date: date
    end_date: date
    points: List[TrendPoint]
    overall_adherence: Optional[float] = None
    data_status: str


# Dashboard Schemas
class DashboardGoalsSummary(BaseModel):
    total: int
    completed: int
    remaining: int
    completion_percentage: float
    items: List[GoalTodayRead] = []


class DashboardAdherenceSummary(BaseModel):
    current_week_percentage: Optional[float] = None
    previous_week_percentage: Optional[float] = None
    percentage_point_delta: Optional[float] = None
    trend_direction: Optional[str] = None
    data_status: str


class HabitMomentumSummary(BaseModel):
    score: Optional[float] = None
    label: str # "Strong", "Steady", "Needs Attention", "Calibrating", "Insufficient Data"
    streak_days: int
    formula_documented: str


class DriftDetectorSummary(BaseModel):
    has_drift: bool
    status: str # "Active", "Stable", "Unavailable - Insufficient Baseline", "No Active Plan"
    baseline_adherence: Optional[float] = None
    current_adherence: Optional[float] = None
    percentage_point_change: Optional[float] = None
    severity: Optional[str] = "Normal" # "Normal", "Low", "Moderate", "High"
    observation_window: Optional[str] = None
    data_sufficiency: Optional[str] = "sufficient"
    flag_reason: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    contributing_observations: List[ContributingObservation] = []
    recovery_proposal_call_to_action: Optional[str] = None
    has_pending_recovery_proposal: bool = False
    pending_recovery_proposal_id: Optional[int] = None
    details: Optional[DriftEventRead] = None


class PatientDashboardResponse(BaseModel):
    patient: PatientBase
    patient_id: int
    active_plan: Optional[WellnessPlanRead] = None
    plan_status: str
    today_goals: DashboardGoalsSummary
    weekly_adherence: DashboardAdherenceSummary
    habit_momentum: HabitMomentumSummary
    recent_measurements: List[MeasurementRead] = []
    profile_completeness: PatientProfileCompleteness
    drift_detector: DriftDetectorSummary
    generated_at: datetime = Field(default_factory=datetime.utcnow)
