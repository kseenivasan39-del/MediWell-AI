from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.wellness_service import get_patient_or_404
from app.services.ai.coach_service import coach_service
from app.services.ai.schemas import (
    CoachMessageRequest,
    CoachResponse,
    CoachSummaryResponse,
    CoachRecoverySuggestionRequest,
)

router = APIRouter(prefix="/patients", tags=["AI Wellness Coach"])


@router.post(
    "/{patient_id}/coach",
    response_model=CoachResponse,
    summary="Interactive AI Wellness Coach dialogue",
)
async def chat_with_coach(
    patient_id: str,
    body: CoachMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Submits a wellness inquiry or check-in to the AI Wellness Coach.

    - Grounded strictly in database-backed patient telemetry.
    - Employs deterministic fallback when external providers are unconfigured, rate-limited, or timed out.
    - Pre-screens for red-flag medical emergencies and prescription medication advice.
    - Generates evidence-linked observations, practical non-prescriptive tips, and barrier follow-ups.
    """
    patient = get_patient_or_404(db, patient_id)
    try:
        response = await coach_service.get_coaching_response(
            db=db,
            patient_id=str(patient.id),
            user_message=body.message,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating coach response: {str(e)}",
        )


@router.get(
    "/{patient_id}/coach/summary",
    response_model=CoachSummaryResponse,
    summary="Get proactive wellness coach summary",
)
async def get_coach_summary(
    patient_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns an educational summary of the patient's current wellness momentum and primary focus area.
    """
    patient = get_patient_or_404(db, patient_id)
    try:
        summary = await coach_service.get_coach_summary(
            db=db,
            patient_id=str(patient.id),
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating coach summary: {str(e)}",
        )


@router.post(
    "/{patient_id}/coach/recovery-suggestion",
    response_model=CoachResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate coaching feedback with a formal reviewable recovery proposal",
)
async def generate_coach_recovery_suggestion(
    patient_id: str,
    body: Optional[CoachRecoverySuggestionRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Generates tailored coaching feedback and initiates a reviewable Phase 3 recovery proposal.
    Does NOT automatically change the active wellness plan.
    """
    patient = get_patient_or_404(db, patient_id)
    custom_notes = body.custom_context if body else None
    try:
        response = await coach_service.generate_recovery_coach_suggestion(
            db=db,
            patient_id=str(patient.id),
            custom_context=custom_notes,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recovery suggestion: {str(e)}",
        )
