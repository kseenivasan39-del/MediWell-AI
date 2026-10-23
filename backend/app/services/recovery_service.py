import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.wellness import (
    Patient,
    WellnessPlan,
    WellnessGoal,
    Habit,
    DriftEvent,
    RecoveryProposal,
)
from app.schemas.wellness import (
    RecoveryProposalRead,
    ProposedAdjustmentItem,
    UserRevisedTargetItem,
)
from app.services.wellness_service import get_active_plan_for_patient


def generate_recovery_proposal(
    db: Session,
    patient_id: int,
    drift_event_id: Optional[int] = None,
    custom_notes: Optional[str] = None,
) -> RecoveryProposal:
    """
    Generates a condition-aware recovery proposal based on:
    - Active wellness plan goals.
    - Observed drift events or declining habits.
    - Recorded patient barriers or timing frictions.

    Purely non-destructive:
    - Returns a proposal for review/approval.
    - NEVER modifies the patient's existing active wellness plan automatically.
    - Never recommends medications or diagnosis changes.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError(f"Patient with ID {patient_id} not found")

    active_plan = get_active_plan_for_patient(db, patient_id)
    if not active_plan:
        raise ValueError(f"Patient {patient.synthetic_identifier} has no active wellness plan")

    drift_event = None
    if drift_event_id:
        drift_event = db.query(DriftEvent).filter(DriftEvent.id == drift_event_id).first()
    if not drift_event:
        drift_event = (
            db.query(DriftEvent)
            .filter(DriftEvent.patient_id == patient_id, DriftEvent.status == "Active")
            .order_by(DriftEvent.created_at.desc())
            .first()
        )

    goals = db.query(WellnessGoal).filter(WellnessGoal.plan_id == active_plan.id).all()
    if not goals:
        raise ValueError("Active wellness plan contains no goals to adapt")

    # Inspect contributing factors from drift event if present
    declining_habit_ids = set()
    barriers_found = []
    if drift_event and drift_event.contributing_factors:
        for factor in drift_event.contributing_factors:
            if factor.get("category") == "habit_decline" and factor.get("habit_id"):
                declining_habit_ids.add(factor["habit_id"])
            if factor.get("category") == "user_reported_barrier" and factor.get("barrier_reported"):
                barriers_found.append(factor["barrier_reported"])

    # If specific declining habits were identified, prioritize up to 2 of them
    target_goals = []
    for g in goals:
        if g.habit_id in declining_habit_ids:
            target_goals.append(g)

    # Fallback: if none flagged or no drift event, take top 2 high/medium priority goals
    if not target_goals:
        target_goals = sorted(goals, key=lambda x: 0 if x.priority == "high" else 1)[:2]
    else:
        target_goals = target_goals[:2]

    proposed_adjustments: List[Dict[str, Any]] = []
    rationale_points: List[str] = []

    for goal in target_goals:
        habit = db.query(Habit).filter(Habit.id == goal.habit_id).first()
        habit_name = habit.name if habit else goal.title

        current_val = goal.target_value
        unit = goal.target_unit or "units"

        # Offer reduced, flexible target to rebuild momentum
        proposed_val = current_val
        adj_type = "reduce_target"

        if current_val and current_val > 0:
            if unit in ["min", "minutes"]:
                # Reduce duration by ~25-30% (e.g. 20 min -> 15 min, 30 min -> 20 min)
                proposed_val = max(10.0, round(current_val * 0.7, 0))
                adj_type = "reduce_target"
            elif unit in ["L", "liters"]:
                # Hydration reduction (e.g. 2.5L -> 2.0L)
                proposed_val = max(1.5, round(current_val * 0.8, 1))
                adj_type = "reduce_target"
            elif unit in ["steps"]:
                proposed_val = max(3000.0, round(current_val * 0.75, -2))
                adj_type = "reduce_target"
            else:
                proposed_val = current_val

        # Timing flexibility suggestion if a strict time was recommended
        suggested_time = goal.recommended_time
        if goal.recommended_time and "AM" in goal.recommended_time:
            suggested_time = "Flexible (Morning or Evening)"
            adj_type = "adjust_schedule"

        proposed_adjustments.append({
            "goal_id": goal.id,
            "habit_id": goal.habit_id,
            "habit_name": habit_name,
            "current_target": current_val,
            "proposed_target": proposed_val,
            "unit": unit,
            "current_frequency": goal.frequency,
            "proposed_frequency": goal.frequency,
            "recommended_time": suggested_time,
            "adjustment_type": adj_type,
        })

        rationale_points.append(
            f"Temporary easing of '{habit_name}' from {current_val} {unit} to {proposed_val} {unit} "
            f"to reduce behavioral friction and stabilize daily adherence."
        )

    title = f"Adaptive Recovery Protocol for {active_plan.plan_name}"
    rationale = " ".join(rationale_points)
    if barriers_found:
        rationale += f" Addresses user-reported friction: {', '.join(barriers_found)}."

    barrier_question = (
        "Would adjusting the routine schedule or target duration help you stay consistent this week?"
    )

    proposal = RecoveryProposal(
        patient_id=patient.id,
        plan_id=active_plan.id,
        drift_event_id=drift_event.id if drift_event else None,
        title=title,
        rationale=rationale,
        status="pending",
        proposed_adjustments=proposed_adjustments,
        barrier_question=barrier_question,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def apply_recovery_decision(
    db: Session,
    proposal_id: int,
    decision: str,
    decision_notes: Optional[str] = None,
    user_revised_targets: Optional[List[UserRevisedTargetItem]] = None,
) -> RecoveryProposal:
    """
    Applies the patient's explicit review decision on a recovery proposal.

    Decisions:
    - 'accepted': Patient agrees to the proposed target adjustments. Active plan goals are updated accordingly.
    - 'edited': Patient customized targets. Active plan goals are updated to patient-specified values.
    - 'rejected': Patient declines adjustments. Plan remains unchanged.

    Safety:
    - Enforces single decision application (cannot apply decision to already resolved proposal).
    - Preserves audit trail in recovery_proposals table.
    - Acknowledges corresponding drift_event if accepted or edited.
    """
    decision = decision.lower().strip()
    if decision not in ["accepted", "edited", "rejected"]:
        raise ValueError("Decision must be one of: 'accepted', 'edited', 'rejected'")

    proposal = db.query(RecoveryProposal).filter(RecoveryProposal.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"Recovery proposal with ID {proposal_id} not found")

    if proposal.status != "pending":
        raise ValueError(f"Recovery proposal #{proposal_id} has already been resolved with status '{proposal.status}'")

    proposal.status = decision
    proposal.decision_notes = decision_notes
    proposal.decided_at = datetime.datetime.utcnow()

    revised_dict = None
    if decision == "edited" and user_revised_targets:
        proposal.user_revised_targets = [item.model_dump() for item in user_revised_targets]
        revised_dict = {item.goal_id: item for item in user_revised_targets}

    # If accepted or edited, update the active wellness plan goals with explicit consent
    if decision in ["accepted", "edited"]:
        for adj in proposal.proposed_adjustments:
            goal_id = adj.get("goal_id")
            goal = db.query(WellnessGoal).filter(WellnessGoal.id == goal_id).first()
            if not goal:
                continue

            if decision == "accepted":
                if adj.get("proposed_target") is not None:
                    goal.target_value = adj["proposed_target"]
                if adj.get("recommended_time"):
                    goal.recommended_time = adj["recommended_time"]
            elif decision == "edited" and revised_dict and goal_id in revised_dict:
                user_item = revised_dict[goal_id]
                if user_item.revised_target is not None:
                    goal.target_value = user_item.revised_target
                if user_item.revised_frequency:
                    goal.frequency = user_item.revised_frequency

        # If linked to an active drift event, transition status to 'Acknowledged'
        if proposal.drift_event_id:
            drift = db.query(DriftEvent).filter(DriftEvent.id == proposal.drift_event_id).first()
            if drift and drift.status == "Active":
                drift.status = "Acknowledged"

    elif decision == "rejected":
        # Keep plan untouched; mark drift event as Acknowledged
        if proposal.drift_event_id:
            drift = db.query(DriftEvent).filter(DriftEvent.id == proposal.drift_event_id).first()
            if drift and drift.status == "Active":
                drift.status = "Acknowledged"

    db.commit()
    db.refresh(proposal)
    return proposal
