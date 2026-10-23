import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import (
    DeterministicFallbackProvider,
    check_urgent_symptoms,
    check_medication_or_diagnosis_request,
)
from app.services.ai.gemini_provider import GeminiAIProvider
from app.services.ai.groq_provider import GroqAIProvider
from app.services.ai.context_builder import assemble_patient_context
from app.services.ai.schemas import CoachResponse, CoachSummaryResponse
from app.services.recovery_service import generate_recovery_proposal

logger = logging.getLogger(__name__)


class AICoachService:
    """
    Orchestrates the AI Wellness Coach lifecycle:
    - Selects the configured primary provider (Gemini, Groq) or falls back gracefully.
    - Assembles sanitized patient telemetry context from the database.
    - Pre-screens for acute emergencies and out-of-scope medication advice.
    - Bounded retries and graceful fallback to DeterministicFallbackProvider.
    """

    def __init__(self):
        self._fallback_provider = DeterministicFallbackProvider()
        self._gemini_provider = GeminiAIProvider()
        self._groq_provider = GroqAIProvider()

    def select_provider(self) -> BaseAIProvider:
        pref = settings.AI_PROVIDER.lower().strip()
        if pref == "gemini" and self._gemini_provider.is_configured():
            return self._gemini_provider
        elif pref == "groq" and self._groq_provider.is_configured():
            return self._groq_provider
        elif pref == "auto":
            # Priority: Gemini -> Groq -> Fallback
            if self._gemini_provider.is_configured():
                return self._gemini_provider
            elif self._groq_provider.is_configured():
                return self._groq_provider

        return self._fallback_provider

    async def get_coaching_response(
        self,
        db: Session,
        patient_id: str,
        user_message: str,
    ) -> CoachResponse:
        """
        Coordinates context assembly, provider execution, and fallback selection.
        """
        # 1. Build ground-truth patient context from persisted database state
        context = assemble_patient_context(db, patient_id)

        # 2. Pre-screen safety keywords: always handle urgent symptoms and drug advice immediately
        if check_urgent_symptoms(user_message) or check_medication_or_diagnosis_request(user_message):
            return await self._fallback_provider.generate_coach_response(context, user_message)

        # 3. Select AI Provider
        provider = self.select_provider()
        timeout = settings.AI_REQUEST_TIMEOUT_SECONDS

        if provider.provider_name == "deterministic_fallback":
            return await provider.generate_coach_response(context, user_message, timeout_seconds=timeout)

        # 4. Attempt external provider call with bounded retry (max 1 retry) and fallback
        for attempt in range(2):
            try:
                response = await provider.generate_coach_response(context, user_message, timeout_seconds=timeout)
                return response
            except Exception as e:
                logger.warning(
                    f"AI provider {provider.provider_name} failed (attempt {attempt + 1}): {e}. "
                    f"{'Retrying once...' if attempt == 0 else 'Falling back to deterministic engine.'}"
                )
                if attempt == 1:
                    break

        # Fallback to local deterministic rules
        fallback_res = await self._fallback_provider.generate_coach_response(context, user_message, timeout_seconds=timeout)
        return fallback_res

    async def get_coach_summary(
        self,
        db: Session,
        patient_id: str,
    ) -> CoachSummaryResponse:
        """
        Returns a concise educational wellness summary and focus area based on current data.
        """
        context = assemble_patient_context(db, patient_id)
        patient = context.get("patient", {})
        analytics = context.get("analytics", {})
        drift = context.get("drift", {})

        has_drift = drift.get("has_drift", False)
        weekly_adh = analytics.get("weekly_adherence_percentage")
        status_label = "Active Drift Alert" if has_drift else ("Stable & On Track" if (weekly_adh and weekly_adh >= 70) else "Routine Calibrating")

        highlights = []
        if weekly_adh is not None:
            highlights.append(f"7-day scheduled goal completion is {weekly_adh}%.")
        if analytics.get("streak_days"):
            highlights.append(f"Current momentum streak: {analytics['streak_days']} days.")
        if has_drift:
            highlights.append("Recent decline detected below historical baseline.")
        if context.get("reported_barriers"):
            highlights.append(f"Recent friction noted: '{context['reported_barriers'][0]['barrier_text']}'.")

        focus_area = None
        if has_drift:
            focus_area = "Reviewing adaptive recovery targets to reduce daily friction."
        elif context.get("active_plan", {}).get("goals"):
            top_goal = context["active_plan"]["goals"][0]
            focus_area = f"Maintaining consistency with '{top_goal['habit_name']}'."
        else:
            focus_area = "Configuring initial wellness protocol."

        provider = self.select_provider()

        return CoachSummaryResponse(
            patient_id=patient.get("id", 0),
            synthetic_identifier=patient.get("synthetic_identifier", "SYNTH-UNKNOWN"),
            display_name=patient.get("display_name", "Patient"),
            overall_wellness_status=status_label,
            key_highlights=highlights,
            recommended_focus_area=focus_area,
            has_active_drift=has_drift,
            pending_recovery_proposal_id=context.get("pending_recovery_proposal", {}).get("id") if context.get("pending_recovery_proposal") else None,
            provider_name=provider.provider_name,
        )

    async def generate_recovery_coach_suggestion(
        self,
        db: Session,
        patient_id: str,
        custom_context: Optional[str] = None,
    ) -> CoachResponse:
        """
        Generates an AI coach reflection accompanied by an actual reviewable RecoveryProposal.
        Integrates directly with Phase 3 recovery service without modifying active plans automatically.
        """
        context = assemble_patient_context(db, patient_id)
        patient = context.get("patient", {})
        drift_event_id = context.get("active_drift_event_id")

        # Create reviewable proposal via Phase 3 recovery service
        proposal = generate_recovery_proposal(
            db=db,
            patient_id=patient.get("id"),
            drift_event_id=drift_event_id,
            custom_notes=custom_context,
        )

        user_msg = (
            f"Please review my recent habit logs and suggest an adaptive recovery approach. "
            f"{custom_context or ''}"
        )
        coach_response = await self.get_coaching_response(db, str(patient.get("id")), user_msg)
        coach_response.recovery_proposal_id = proposal.id
        coach_response.recovery_proposal_title = proposal.title
        return coach_response


coach_service = AICoachService()
