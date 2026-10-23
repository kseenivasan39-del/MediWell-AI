import json
import asyncio
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.ai.base import BaseAIProvider
from app.services.ai.schemas import CoachResponse

SYSTEM_INSTRUCTION = """
You are the MediWell AI Wellness Coach, an empathetic, evidence-linked assistant for preventive wellness and habit consistency.

CORE RULES & SCOPE:
1. Provide personalized preventive wellness reflections and supportive habit cues.
2. YOU ARE NOT A DOCTOR: Never diagnose conditions, predict medical outcomes, or recommend prescription medications / dosage changes.
3. If the user presents emergency red-flag symptoms (chest pain, shortness of breath, severe dizziness, stroke symptoms), set is_urgent_guidance=true and urge them to call 911/emergency care immediately.
4. If the user asks for diagnosis or drug advice, politely decline, remind them of your wellness scope, and urge consultation with their prescribing doctor.
5. NO INVENTED EVIDENCE: You must strictly cite recorded facts present in the provided context (dates, logged barriers, adherence percentages, metrics). Never fabricate unrecorded logs.
6. Observations must specify observation_type: 'observed' (facts in context), 'possible_explanation' (hypotheses), or 'suggestion' (non-prescriptive ideas).
7. Respond strictly in the specified JSON schema matching CoachResponse.
"""


class GeminiAIProvider(BaseAIProvider):
    """
    Google Gemini provider using official google-genai SDK.
    Supports structured outputs with Pydantic schemas.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._client: Optional[genai.Client] = None
        if self._api_key:
            self._client = genai.Client(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def is_configured(self) -> bool:
        return bool(self._api_key and self._client)

    async def generate_coach_response(
        self,
        patient_context: Dict[str, Any],
        user_message: str,
        timeout_seconds: float = 12.0,
    ) -> CoachResponse:
        if not self.is_configured():
            raise RuntimeError("Gemini provider is not configured with an API key.")

        patient_id = patient_context.get("patient", {}).get("id", 0)
        synthetic_id = patient_context.get("patient", {}).get("synthetic_identifier", "SYNTH-UNKNOWN")

        prompt = (
            f"PATIENT CONTEXT (Ground truth facts from database - DO NOT INVENT OUTSIDE THIS):\n"
            f"{json.dumps(patient_context, indent=2)}\n\n"
            f"PATIENT MESSAGE:\n"
            f"\"{user_message}\"\n\n"
            f"Generate a helpful, empathetic, evidence-grounded wellness coach response."
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",
            response_schema=CoachResponse,
        )

        # Call in executor with timeout to keep async FastAPI loop responsive
        loop = asyncio.get_running_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    ),
                ),
                timeout=timeout_seconds,
            )

            if not response.text:
                raise ValueError("Empty response received from Gemini.")

            data = json.loads(response.text)
            # Ensure correct identity and provider metadata
            data["patient_id"] = patient_id
            data["synthetic_identifier"] = synthetic_id
            data["provider_name"] = self.provider_name
            data["model_name"] = self.model_name
            return CoachResponse.model_validate(data)

        except asyncio.TimeoutError:
            raise TimeoutError(f"Gemini API request timed out after {timeout_seconds} seconds.")
        except Exception as e:
            raise RuntimeError(f"Gemini provider error: {str(e)}") from e
