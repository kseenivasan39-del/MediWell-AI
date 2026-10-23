from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "MediWell AI — Preventive Wellness Platform"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./mediwell.db"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"

    # Drift Detector Configuration
    DRIFT_BASELINE_DAYS: int = 21
    DRIFT_RECENT_DAYS: int = 7
    DRIFT_MIN_OCCURRENCES: int = 5
    DRIFT_ALERT_THRESHOLD_PCT: float = 15.0

    # AI Wellness Coach Configuration
    AI_PROVIDER: str = "auto" # "auto", "gemini", "groq", "vertex", "fallback"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-3.5-flash-lite"
    AI_REQUEST_TIMEOUT_SECONDS: float = 12.0
    AI_MAX_OUTPUT_TOKENS: int = 1024

    # Google Calendar OAuth & Sync Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/calendar/callback"
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CALENDAR_TIMEZONE: str = "Asia/Kolkata"
    CALENDAR_TOKEN_ENCRYPTION_KEY: str = "" # 32-byte urlsafe base64 Fernet key or auto-derived

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
