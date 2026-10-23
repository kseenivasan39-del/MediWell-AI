from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.services.ai.schemas import CoachResponse


class BaseAIProvider(ABC):
    """
    Abstract interface for AI Wellness Coach provider implementations.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'groq', 'deterministic_fallback')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier being used."""
        pass

    @abstractmethod
    async def generate_coach_response(
        self,
        patient_context: Dict[str, Any],
        user_message: str,
        timeout_seconds: float = 12.0,
    ) -> CoachResponse:
        """
        Generates structured, validated wellness coaching response.
        Must enforce non-prescriptive, safe behavior and never invent evidence.
        """
        pass
