"""Database initialization and utilities."""
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy Supabase client (only initialize if settings are provided)
_supabase_client: Client = None

def get_supabase() -> Client:
    """Get Supabase client (lazy initialization)."""
    global _supabase_client

    if not settings.supabase_url or not settings.supabase_anon_key:
        logger.warning("Supabase credentials not configured. Database operations will fail.")
        return None

    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )

    return _supabase_client

def get_supabase_service_role() -> Client:
    """Get Supabase client with service role (admin) access."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase credentials not configured. Database operations will fail.")
        return None

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

# SQLAlchemy async engine (optional, for direct DB access if needed)
# TODO: Use this if building ORM queries directly to Postgres
# DATABASE_URL = f"postgresql+asyncpg://user:password@host/db"
# engine = create_async_engine(DATABASE_URL, echo=settings.debug)
# async_session_factory = sessionmaker(
#     engine, class_=AsyncSession, expire_on_commit=False
# )

def init_db():
    """Initialize database (run migrations, etc)."""
    logger.info("Initializing database...")
    # TODO: Run Supabase migrations via CLI
    # For now, migrations are applied via supabase/migrations/*.sql
    logger.info("Database initialized")

async def get_session():
    """Get async database session."""
    # TODO: If using SQLAlchemy ORM directly
    # async with async_session_factory() as session:
    #     yield session
    pass

def execute_query(query: str, params: dict = None):
    """Execute raw SQL query via Supabase."""
    # Use supabase.rpc() for stored procedures or direct SQL
    # For now, data operations go through Supabase client
    pass
