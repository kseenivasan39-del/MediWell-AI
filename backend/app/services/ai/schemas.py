from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

ObservationType = Literal["observed", "possible_explanation", "suggestion"]


class EvidenceLinkedObservation(BaseModel):
    category: str = Field(..., description="E.g. habit_adherence, reported_barrier, timing_pattern, biometric")
    observation_type: ObservationType = Field(
        ...,
        description="'observed' (directly backed by recorded logs), 'possible_explanation' (hypothesis), or 'suggestion' (non-prescriptive wellness option)"
    )
    statement: str = Field(..., description="Clear, non-prescriptive, supportive explanation")
    evidence_reference: Optional[str] = Field(
        None,
        description="Explicit citation of dates, logged barriers, or metrics present in the assembled context"
    )


class PracticalSuggestion(BaseModel):
    title: str = Field(..., description="Actionable wellness tip title")
    description: str = Field(..., description="Practical adjustment or behavioral cue")
    rationale: str = Field(..., description="How this connects to observed habits or barriers")


class CoachMessageRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="Patient question, check-in, or reflection")
    conversation_id: Optional[str] = Field(None, max_length=128, description="Optional client session identifier")


class CoachRecoverySuggestionRequest(BaseModel):
    custom_context: Optional[str] = Field(None, max_length=1000, description="Optional extra notes from patient")


class CoachResponse(BaseModel):
    patient_id: int
    synthetic_identifier: str
    summary: str
    observations: List[EvidenceLinkedObservation] = Field(default_factory=list)
    practical_suggestions: List[PracticalSuggestion] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    recovery_proposal_id: Optional[int] = None
    recovery_proposal_title: Optional[str] = None
    data_sufficiency: str = Field(
        ...,
        description="'sufficient', 'insufficient_history', 'no_active_goals', or 'sparse_data'"
    )
    safety_notice: str = Field(
        default="MediWell AI provides personalized preventive wellness suggestions. It is not a diagnostic tool or substitute for professional medical care."
    )
    is_urgent_guidance: bool = Field(
        default=False,
        description="True if user mentioned red flag/emergency symptoms requiring immediate medical evaluation"
    )
    provider_name: str = Field(..., description="AI provider used (e.g. gemini, groq, deterministic_fallback)")
    model_name: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class CoachSummaryResponse(BaseModel):
    patient_id: int
    synthetic_identifier: str
    display_name: str
    overall_wellness_status: str
    key_highlights: List[str] = Field(default_factory=list)
    recommended_focus_area: Optional[str] = None
    has_active_drift: bool = False
    pending_recovery_proposal_id: Optional[int] = None
    provider_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
