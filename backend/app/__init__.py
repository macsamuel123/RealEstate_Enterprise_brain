"""AI Chief of Staff Backend."""
from app.config import settings
from app.database import get_supabase

__version__ = "0.1.0"

__all__ = ["settings", "get_supabase"]
