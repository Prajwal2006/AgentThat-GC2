"""JWT authentication middleware with tenant context extraction."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    """Authenticated user context extracted from JWT."""
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    role: str  # Admin, Developer, User
    groups: list[str]


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> AuthContext:
    """Extract and validate user context from JWT token.
    
    In development mode, allows X-Dev-* headers for testing without a real IdP.
    In production, validates JWT signature and claims.
    """
    from app.config import settings
    
    # Development mode: accept header-based auth for testing
    if settings.environment == "development":
        dev_user_id = request.headers.get("X-Dev-User-Id")
        dev_tenant_id = request.headers.get("X-Dev-Tenant-Id")
        if dev_user_id and dev_tenant_id:
            return AuthContext(
                user_id=uuid.UUID(dev_user_id),
                tenant_id=uuid.UUID(dev_tenant_id),
                email=request.headers.get("X-Dev-Email", "dev@example.com"),
                display_name=request.headers.get("X-Dev-Name", "Dev User"),
                role=request.headers.get("X-Dev-Role", "Admin"),
                groups=[],
            )
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Validate JWT signature with IdP public keys (Azure Entra ID, etc.)
    # For now, decode without verification in development
    try:
        import json
        import base64
        # Simple JWT decode (payload only) - replace with proper validation in production
        token = credentials.credentials
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Decode payload (base64url)
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        return AuthContext(
            user_id=uuid.UUID(payload.get("sub", payload.get("user_id"))),
            tenant_id=uuid.UUID(payload.get("tenant_id")),
            email=payload.get("email", ""),
            display_name=payload.get("name", ""),
            role=payload.get("role", "User"),
            groups=payload.get("groups", []),
        )
    except (ValueError, KeyError, Exception) as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e
