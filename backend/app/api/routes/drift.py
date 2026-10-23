from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.wellness import DriftEvent, Patient, RecoveryProposal
from app.schemas.wellness import (
    DriftAnalysisResponse,
    DriftAnalyzeRequest,
    DriftEventRead,
    RecoveryProposalCreate,
    RecoveryProposalDecision,
    RecoveryProposalRead,
)
from app.services.wellness_service import get_patient_or_404
from app.services.drift_detector import run_drift_analysis
from app.services.recovery_service import (
    generate_recovery_proposal,
    apply_recovery_decision,
)

router = APIRouter(tags=["Wellness Drift Detector & Recovery"])


# ============================================================================
# Drift Analysis & History Endpoints
# ============================================================================

@router.get(
    "/patients/{patient_id}/drift",
    response_model=DriftAnalysisResponse,
    summary="Get current drift status without persisting new events",
)
def get_patient_drift_status(
    patient_id: str,
    recent_days: Optional[int] = Query(None, ge=1, le=60),
    baseline_days: Optional[int] = Query(None, ge=1, le=180),
    threshold_percentage_points: Optional[float] = Query(None, ge=1.0, le=50.0),
    db: Session = Depends(get_db),
):
    """
    Evaluates current wellness drift status for a patient using deterministic formulas.
    Read-only operation: does not mutate or persist duplicate records.
    """
    patient = get_patient_or_404(db, patient_id)
    try:
        analysis = run_drift_analysis(
            db=db,
            patient_id=patient.id,
            recent_days=recent_days,
            baseline_days=baseline_days,
            threshold_percentage_points=threshold_percentage_points,
            persist_event=False,
        )
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/patients/{patient_id}/drift/analyze",
    response_model=DriftAnalysisResponse,
    summary="Run drift analysis and idempotently persist active drift events",
)
def analyze_patient_drift(
    patient_id: str,
    body: Optional[DriftAnalyzeRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Executes a formal drift analysis against stored habit telemetry and persists an active
    DriftEvent if the decline meets the alert threshold.
    Guarantees idempotency: running repeated analyses for the same window updates the record
    instead of producing duplicate events.
    """
    patient = get_patient_or_404(db, patient_id)
    req = body or DriftAnalyzeRequest()
    try:
        analysis = run_drift_analysis(
            db=db,
            patient_id=patient.id,
            recent_days=req.recent_days,
            baseline_days=req.baseline_days,
            threshold_percentage_points=req.threshold_percentage_points,
            persist_event=req.persist_event,
        )
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/patients/{patient_id}/drift/history",
    response_model=List[DriftEventRead],
    summary="List historical drift events for a patient",
)
def get_patient_drift_history(
    patient_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns audit trail of persisted drift events ordered by creation timestamp.
    """
    patient = get_patient_or_404(db, patient_id)
    events = (
        db.query(DriftEvent)
        .filter(DriftEvent.patient_id == patient.id)
        .order_by(DriftEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return events


# ============================================================================
# Recovery Plan Proposals Endpoints
# ============================================================================

@router.post(
    "/patients/{patient_id}/recovery-proposals",
    response_model=RecoveryProposalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a non-destructive recovery plan proposal",
)
def create_recovery_proposal(
    patient_id: str,
    body: Optional[RecoveryProposalCreate] = None,
    db: Session = Depends(get_db),
):
    """
    Generates an adaptive recovery proposal linked to observed drift or declining habits.
    Does not modify the active plan until patient reviews and submits an explicit decision.
    """
    patient = get_patient_or_404(db, patient_id)
    req = body or RecoveryProposalCreate()
    try:
        proposal = generate_recovery_proposal(
            db=db,
            patient_id=patient.id,
            drift_event_id=req.drift_event_id,
            custom_notes=req.custom_notes,
        )
        return proposal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/patients/{patient_id}/recovery-proposals",
    response_model=List[RecoveryProposalRead],
    summary="List recovery proposals for a patient",
)
def list_recovery_proposals(
    patient_id: str,
    status_filter: Optional[str] = Query(None, pattern="^(pending|accepted|edited|rejected)$"),
    db: Session = Depends(get_db),
):
    """
    Lists recovery proposals created for a patient, optionally filtered by status.
    """
    patient = get_patient_or_404(db, patient_id)
    query = db.query(RecoveryProposal).filter(RecoveryProposal.patient_id == patient.id)
    if status_filter:
        query = query.filter(RecoveryProposal.status == status_filter)
    proposals = query.order_by(RecoveryProposal.created_at.desc()).all()
    return proposals


@router.post(
    "/recovery-proposals/{proposal_id}/decision",
    response_model=RecoveryProposalRead,
    summary="Submit patient decision on a recovery proposal",
)
def submit_recovery_decision(
    proposal_id: int,
    body: RecoveryProposalDecision,
    db: Session = Depends(get_db),
):
    """
    Applies the patient's explicit review decision on a proposal.
    - 'accepted': Updates the active plan goals with proposed targets.
    - 'edited': Updates the active plan goals with user-revised targets.
    - 'rejected': Leaves the active plan untouched.
    Enforces idempotency and prevents applying a decision twice.
    """
    proposal = db.query(RecoveryProposal).filter(RecoveryProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery proposal with ID {proposal_id} not found",
        )

    try:
        updated = apply_recovery_decision(
            db=db,
            proposal_id=proposal_id,
            decision=body.decision,
            decision_notes=body.decision_notes,
            user_revised_targets=body.user_revised_targets,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
