"""Authentication and authorization middleware."""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class TokenPayload:
    """Parsed JWT token."""
    def __init__(self, user_id: UUID, org_id: UUID, email: str, role: str):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role

async def verify_token_middleware(request: Request, call_next):
    """
    Middleware to verify JWT token from Supabase Auth.
    TODO: Implement actual verification once Supabase Auth is set up.
    """
    # For now, this is a placeholder
    # In production:
    # 1. Extract token from Authorization header
    # 2. Verify with Supabase Auth (public key)
    # 3. Extract org_id from token claims
    # 4. Store in request.state for later use

    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            # TODO: Verify token with Supabase Auth
            # request.state.token_payload = verify_jwt_token(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

    response = await call_next(request)
    return response

def get_token_payload(request: Request) -> Optional[TokenPayload]:
    """Extract token payload from request state."""
    return getattr(request.state, "token_payload", None)

def require_auth(request: Request) -> TokenPayload:
    """Require authentication for a route."""
    payload = get_token_payload(request)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return payload

def require_org_access(request: Request, org_id: UUID) -> TokenPayload:
    """Require access to a specific organization."""
    payload = require_auth(request)
    if payload.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    return payload

def require_role(request: Request, required_role: str) -> TokenPayload:
    """Require a specific role."""
    payload = require_auth(request)
    # Role hierarchy: owner > admin > member > viewer
    role_hierarchy = {"owner": 4, "admin": 3, "member": 2, "viewer": 1}

    if role_hierarchy.get(payload.role, 0) < role_hierarchy.get(required_role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return payload
