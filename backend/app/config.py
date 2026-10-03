from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"

    # Supabase (optional for dev, required for prod)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # LLM (optional for dev)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    # Google OAuth (optional for dev)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Voice (optional for dev)
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Twilio (optional for dev)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # Stripe (optional for dev)
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Web Search (optional for dev)
    serpapi_key: Optional[str] = None

    # Zapier (optional for dev)
    zapier_webhook_urls: Optional[str] = None

    # CRM (optional for dev)
    crm_api_key: Optional[str] = None
    crm_type: Optional[str] = None

    # Deployment (optional for dev)
    railway_api_token: Optional[str] = None
    vercel_token: Optional[str] = None

    # Database
    database_log_level: str = "info"

    # Frontend
    frontend_url: str = "http://localhost:5173"
    vite_api_url: Optional[str] = None
    vite_supabase_url: Optional[str] = None
    vite_supabase_anon_key: Optional[str] = None

    # API
    api_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
