"""FastAPI app entry point for AI Chief of Staff backend."""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.config import settings
from app.database import init_db, get_session
from app.auth.middleware import verify_token_middleware

# Configure logging
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Chief of Staff API",
    description="Backend for AI Chief of Staff - Real Estate Edition",
    version="0.1.0",
    debug=settings.debug
)

# ============================================================================
# MIDDLEWARE
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add request metadata for logging and tracing."""
    request.state.request_id = request.headers.get("X-Request-ID", f"req_{datetime.utcnow().timestamp()}")
    request.state.user_id = None  # Will be set by auth middleware
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================
@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    logger.info(f"Starting AI Chief of Staff backend (env={settings.environment})")
    logger.info(f"Supabase URL: {settings.supabase_url}")
    # TODO: init_db() if using SQLAlchemy directly
    logger.info("Backend started successfully")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down backend")

# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }

# ============================================================================
# ROOT
# ============================================================================
@app.get("/")
async def root():
    """API root."""
    return {
        "name": "AI Chief of Staff API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# ============================================================================
# ROUTERS (to be added)
# ============================================================================
# TODO: Import and include routers:
# from app.routers import auth, briefs, agents, conversations, tools, contacts, deals
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(briefs.router, prefix="/api/briefs", tags=["briefs"])
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# ... etc

# ============================================================================
# ERROR HANDLERS
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "request_id": request.state.request_id
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": 500,
            "request_id": request.state.request_id
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
