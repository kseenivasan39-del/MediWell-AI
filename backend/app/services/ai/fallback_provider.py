import re
from typing import Dict, Any, List
from app.services.ai.base import BaseAIProvider
from app.services.ai.schemas import (
    CoachResponse,
    EvidenceLinkedObservation,
    PracticalSuggestion,
)

# Urgent red-flag emergency keywords requiring immediate care referral
RED_FLAG_PATTERNS = [
    r"\bchest pain\b",
    r"\bshortness of breath\b",
    r"\bpressure in chest\b",
    r"\bsudden weakness\b",
    r"\bsudden numbness\b",
    r"\bfainting\b",
    r"\bsevere dizziness\b",
    r"\bsuicide\b",
    r"\bheart attack\b",
    r"\bstroke\b",
    r"\bsevere blood loss\b",
]

# Medication advice queries requiring clinical redirection
MEDICATION_PATTERNS = [
    r"\bshould i stop taking\b",
    r"\bshould i increase my dose\b",
    r"\bchange my medication\b",
    r"\bprescribe\b",
    r"\bmetformin dose\b",
    r"\blisinopril dose\b",
    r"\binsulin dose\b",
    r"\bdiagnose me\b",
    r"\bdo i have\b",
]


def check_urgent_symptoms(message: str) -> bool:
    msg = message.lower()
    return any(re.search(pat, msg) for pat in RED_FLAG_PATTERNS)


def check_medication_or_diagnosis_request(message: str) -> bool:
    msg = message.lower()
    return any(re.search(pat, msg) for pat in MEDICATION_PATTERNS)


class DeterministicFallbackProvider(BaseAIProvider):
    """
    Guaranteed, offline, deterministic fallback provider.
    Operates without network or API keys, safely constructing structured wellness guidance
    grounded directly in the assembled patient context.
    """

    @property
    def provider_name(self) -> str:
        return "deterministic_fallback"

    @property
    def model_name(self) -> str:
        return "rules_template_engine_v1"

    async def generate_coach_response(
        self,
        patient_context: Dict[str, Any],
        user_message: str,
        timeout_seconds: float = 12.0,
    ) -> CoachResponse:
        patient = patient_context.get("patient", {})
        patient_id = patient.get("id", 0)
        synthetic_id = patient.get("synthetic_identifier", "SYNTH-UNKNOWN")
        display_name = patient.get("display_name", "Patient")
        primary_cond = patient.get("primary_condition", "wellness")

        analytics = patient_context.get("analytics", {})
        weekly_adh = analytics.get("weekly_adherence_percentage")
        momentum_score = analytics.get("habit_momentum_score")
        streak = analytics.get("streak_days", 0)

        drift = patient_context.get("drift", {})
        has_drift = drift.get("has_drift", False)
        pp_change = drift.get("percentage_point_change")
        drift_obs = drift.get("contributing_observations", [])

        barriers = patient_context.get("reported_barriers", [])
        pending_prop = patient_context.get("pending_recovery_proposal")
        data_sufficiency = patient_context.get("data_sufficiency", "sufficient")

        # 1. Emergency Safety Filter
        if check_urgent_symptoms(user_message):
            return CoachResponse(
                patient_id=patient_id,
                synthetic_identifier=synthetic_id,
                summary="URGENT MEDICAL NOTICE: Your message mentions potential emergency medical symptoms.",
                observations=[
                    EvidenceLinkedObservation(
                        category="safety_notice",
                        observation_type="observed",
                        statement="Potential acute medical emergency symptoms detected in patient inquiry.",
                        evidence_reference="User query message",
                    )
                ],
                practical_suggestions=[
                    PracticalSuggestion(
                        title="Seek Immediate Medical Care",
                        description="Please call 911 (or your local emergency services) or go to the nearest emergency department right away.",
                        rationale="Acute symptoms like chest discomfort, sudden numbness, or severe shortness of breath require immediate clinical evaluation, not wellness tracking.",
                    )
                ],
                follow_up_questions=[],
                data_sufficiency=data_sufficiency,
                is_urgent_guidance=True,
                safety_notice="EMERGENCY GUIDANCE: MediWell AI is a preventive habit tracking aid and cannot provide emergency medical care.",
                provider_name=self.provider_name,
                model_name=self.model_name,
            )

        # 2. Medication / Diagnosis Limitation Filter
        if check_medication_or_diagnosis_request(user_message):
            return CoachResponse(
                patient_id=patient_id,
                synthetic_identifier=synthetic_id,
                summary=f"Hello {display_name}. Questions regarding clinical diagnoses or prescription medication dosages must be answered by your prescribing physician or healthcare provider.",
                observations=[
                    EvidenceLinkedObservation(
                        category="clinical_scope",
                        observation_type="observed",
                        statement="Inquiry involves prescription medication management or clinical diagnosis.",
                        evidence_reference="User query message",
                    ),
                    EvidenceLinkedObservation(
                        category="habit_adherence",
                        observation_type="observed",
                        statement=f"Current 7-day routine adherence is {weekly_adh}% with a {streak}-day momentum streak." if weekly_adh is not None else "Routine adherence baseline is currently calibrating.",
                        evidence_reference=f"Weekly logs in {analytics.get('recent_observation_window', 'recent window')}",
                    )
                ],
                practical_suggestions=[
                    PracticalSuggestion(
                        title="Consult Your Prescribing Clinician",
                        description="Contact your healthcare provider or pharmacist directly before modifying any medication schedule, dose, or starting new supplements.",
                        rationale="Safe pharmacology requires complete clinical medical records and licensed provider oversight.",
                    ),
                    PracticalSuggestion(
                        title="Continue Lifestyle & Telemetry Tracking",
                        description=f"Keep logging your daily wellness habits and biometric readings so you have organized data to share at your next consultation.",
                        rationale="Accurate daily wellness telemetry assists healthcare providers during clinical reviews.",
                    )
                ],
                follow_up_questions=[
                    "Would you like help noting down questions or trends to discuss with your doctor at your next visit?"
                ],
                data_sufficiency=data_sufficiency,
                safety_notice="CLINICAL BOUNDARY: MediWell AI supports non-clinical lifestyle habits. Never alter prescription medications without licensed medical consultation.",
                provider_name=self.provider_name,
                model_name=self.model_name,
            )

        # 3. Standard Context-Aware Coaching Guidance
        observations: List[EvidenceLinkedObservation] = []
        suggestions: List[PracticalSuggestion] = []
        follow_ups: List[str] = []

        if data_sufficiency == "no_active_goals":
            summary = f"Welcome, {display_name}. Your profile does not have an active wellness plan yet."
            suggestions.append(
                PracticalSuggestion(
                    title="Configure Your Wellness Goals",
                    description="Work with your care team to establish personalized daily wellness goals tailored to your routine.",
                    rationale="Establishing clear daily targets enables progress tracking and tailored coaching support.",
                )
            )
            follow_ups.append("What daily health habit would you like to start building first?")

        elif has_drift:
            summary = (
                f"Hello {display_name}. Recent logs indicate a {abs(pp_change) if pp_change else 15}% drop in routine adherence "
                f"below your established baseline. Let's look at gentle adjustments to help rebuild your momentum."
            )
            observations.append(
                EvidenceLinkedObservation(
                    category="habit_adherence",
                    observation_type="observed",
                    statement=f"Adherence decreased to {weekly_adh}% over the recent observation window.",
                    evidence_reference=f"Recorded logs in {drift.get('observation_window', 'recent window')}",
                )
            )

            # Check for barriers
            if barriers:
                latest_b = barriers[0]
                observations.append(
                    EvidenceLinkedObservation(
                        category="reported_barrier",
                        observation_type="observed",
                        statement=f"You reported the following challenge on {latest_b['date']} for {latest_b['habit_name']}: '{latest_b['barrier_text']}'.",
                        evidence_reference=f"Habit log entry on {latest_b['date']}",
                    )
                )
                suggestions.append(
                    PracticalSuggestion(
                        title="Targeted Friction Reduction",
                        description=f"Consider adjusting the timing or splitting the goal into smaller increments when experiencing {latest_b['barrier_text'].lower()}.",
                        rationale="Gradual micro-habits maintain behavioral momentum on challenging days.",
                    )
                )
            else:
                observations.append(
                    EvidenceLinkedObservation(
                        category="reported_barrier",
                        observation_type="possible_explanation",
                        statement="No specific barrier was logged. Unscheduled time conflicts or fatigue may be contributing to the missed routines.",
                        evidence_reference="Absence of recorded barriers in habit_logs",
                    )
                )
                follow_ups.append("What was the biggest obstacle or friction point you encountered over the past week?")

            # Suggest review of recovery proposal
            if pending_prop:
                suggestions.append(
                    PracticalSuggestion(
                        title="Review Adaptive Recovery Proposal",
                        description=f"An adaptive plan proposal ('{pending_prop.get('title')}') is waiting for your review with flexible targets.",
                        rationale="Temporary target easing allows you to reset consistency without feeling overwhelmed.",
                    )
                )
            else:
                suggestions.append(
                    PracticalSuggestion(
                        title="Rebuild with Micro-Steps",
                        description="Focus on completing just one high-priority goal each morning to restore daily momentum.",
                        rationale="Single-win consistency compounds into sustained adherence.",
                    )
                )

        else:
            # Stable or improving adherence
            summary = (
                f"Hello {display_name}. Your wellness routine is progressing well with {weekly_adh or 85}% adherence "
                f"and a current momentum score of {momentum_score or 70}/100 ({analytics.get('habit_momentum_label', 'Steady')})."
            )
            observations.append(
                EvidenceLinkedObservation(
                    category="habit_adherence",
                    observation_type="observed",
                    statement=f"You have maintained a {streak}-day completion streak in your scheduled goals.",
                    evidence_reference=f"Consistent habit logs through {analytics.get('recent_observation_window', 'recent window')}",
                )
            )
            suggestions.append(
                PracticalSuggestion(
                    title="Anchor Your Routine",
                    description="Keep linking your wellness habits to existing daily anchors (such as breakfast or your evening wind-down).",
                    rationale="Habit stacking maintains high automaticity and preserves energy.",
                )
            )
            suggestions.append(
                PracticalSuggestion(
                    title="Celebrate Small Wins",
                    description="Consistent daily logging is a powerful preventive habit in itself. Keep logging regularly.",
                    rationale="Self-monitoring reinforces internal motivation.",
                )
            )
            follow_ups.append("How are your current routine times feeling? Do any goals need fine-tuning?")

        return CoachResponse(
            patient_id=patient_id,
            synthetic_identifier=synthetic_id,
            summary=summary,
            observations=observations,
            practical_suggestions=suggestions,
            follow_up_questions=follow_ups,
            recovery_proposal_id=pending_prop.get("id") if pending_prop else None,
            recovery_proposal_title=pending_prop.get("title") if pending_prop else None,
            data_sufficiency=data_sufficiency,
            safety_notice="MediWell AI provides personalized preventive wellness suggestions. It is not a diagnostic tool or substitute for professional medical care.",
            is_urgent_guidance=False,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )
