"""Database initialization and utilities."""
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Supabase client (for direct access)
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

def get_supabase() -> Client:
    """Get Supabase client."""
    return supabase

def get_supabase_service_role() -> Client:
    """Get Supabase client with service role (admin) access."""
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
