from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # LLM
    anthropic_api_key: str
    openai_api_key: str

    # Google OAuth
    google_client_id: str
    google_client_secret: str

    # Voice
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "default"

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Stripe
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str

    # Database
    database_log_level: str = "info"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # API
    api_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
