import json
import asyncio
from typing import Dict, Any, Optional
from groq import AsyncGroq

from app.core.config import settings
from app.services.ai.base import BaseAIProvider
from app.services.ai.schemas import CoachResponse

SYSTEM_PROMPT = """
You are the MediWell AI Wellness Coach, an empathetic, evidence-linked assistant for preventive wellness and habit consistency.

CORE RULES:
1. Provide personalized preventive wellness suggestions.
2. NOT A DOCTOR: Never diagnose conditions or advise on prescription drugs.
3. If urgent symptoms (chest pain, shortness of breath, severe dizziness) appear, direct immediately to emergency services.
4. Strict factual grounding: Do not invent unlogged data or unrecorded barriers.
5. You must output raw JSON adhering to the CoachResponse schema.
"""


class GroqAIProvider(BaseAIProvider):
    """
    Groq provider using official AsyncGroq SDK.
    High-speed inference with JSON mode.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.GROQ_API_KEY
        self._model = model or settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        self._client: Optional[AsyncGroq] = None
        if self._api_key:
            self._client = AsyncGroq(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "groq"

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
            raise RuntimeError("Groq provider is not configured with an API key.")

        patient_id = patient_context.get("patient", {}).get("id", 0)
        synthetic_id = patient_context.get("patient", {}).get("synthetic_identifier", "SYNTH-UNKNOWN")

        prompt = (
            f"PATIENT CONTEXT:\n{json.dumps(patient_context, indent=2)}\n\n"
            f"PATIENT MESSAGE:\n\"{user_message}\"\n\n"
            f"Respond with a JSON object conforming strictly to CoachResponse schema."
        )

        try:
            chat_completion = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
                    temperature=0.3,
                ),
                timeout=timeout_seconds,
            )

            content = chat_completion.choices[0].message.content
            if not content:
                raise ValueError("Empty response received from Groq.")

            data = json.loads(content)
            data["patient_id"] = patient_id
            data["synthetic_identifier"] = synthetic_id
            data["provider_name"] = self.provider_name
            data["model_name"] = self.model_name
            return CoachResponse.model_validate(data)

        except asyncio.TimeoutError:
            raise TimeoutError(f"Groq API request timed out after {timeout_seconds} seconds.")
        except Exception as e:
            raise RuntimeError(f"Groq provider error: {str(e)}") from e
