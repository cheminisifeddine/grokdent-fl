"""
GrokDent FL - Application Configuration
Uses Pydantic Settings for type-safe environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # --- Application ---
    APP_NAME: str = Field(default="GrokDent FL", description="Application name")
    DEBUG: bool = Field(default=True, description="Debug mode toggle")
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars",
        description="JWT signing key — MUST be changed in production",
    )

    # --- Database ---
    DATABASE_URL: str = Field(
        default="sqlite:///./grokdent.db",
        description="Database connection string",
    )

    # --- Encryption (HIPAA) ---
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet key for encrypting PHI at rest",
    )

    # --- xAI / Grok API ---
    XAI_API_KEY: str = Field(default="", description="xAI API key for Grok")
    XAI_BASE_URL: str = Field(
        default="https://api.x.ai/v1",
        description="xAI API base URL",
    )

    # --- Twilio ---
    TWILIO_ACCOUNT_SID: str = Field(default="", description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", description="Twilio Auth Token")
    TWILIO_PHONE_NUMBER: str = Field(default="", description="Twilio phone number")

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = Field(default="", description="Stripe secret key")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", description="Stripe webhook secret")

    # --- SendGrid ---
    SENDGRID_API_KEY: str = Field(default="", description="SendGrid API key")

    # --- Google Calendar ---
    GOOGLE_CALENDAR_CREDENTIALS_JSON: str = Field(
        default="{}",
        description="Google service-account credentials JSON (single line)",
    )
    GOOGLE_CALENDAR_ID: str = Field(
        default="primary",
        description="Google Calendar ID to sync with",
    )

    # --- Cal.com Scheduling ---
    CALCOM_API_KEY: Optional[str] = Field(
        default=None,
        description="Cal.com API Key",
    )
    CALCOM_EVENT_TYPE_ID: Optional[int] = Field(
        default=None,
        description="Cal.com Event Type ID to check slots and book",
    )
    CALCOM_API_URL: str = Field(
        default="https://api.cal.com/v1",
        description="Cal.com API base URL",
    )

    # --- Calendly Scheduling ---
    CALENDLY_PAT: Optional[str] = Field(
        default=None,
        description="Calendly Personal Access Token (PAT)",
    )
    CALENDLY_EVENT_TYPE_URI: Optional[str] = Field(
        default=None,
        description="Calendly Event Type URI to check slots and book",
    )
    CALENDLY_API_URL: str = Field(
        default="https://api.calendly.com",
        description="Calendly API base URL",
    )

    # --- JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=480,
        description="JWT access token lifetime in minutes (8 hours default)",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8000",
        description="Comma-separated allowed CORS origins",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance
settings = Settings()
