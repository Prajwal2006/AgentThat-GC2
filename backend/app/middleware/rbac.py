"""Role-Based Access Control middleware."""
from __future__ import annotations

from functools import wraps
from typing import Callable

from fastapi import HTTPException

from app.middleware.auth import AuthContext

# Role hierarchy: Admin > Developer > User
ROLE_HIERARCHY = {
    "Admin": 3,
    "Developer": 2,
    "User": 1,
}


def get_role_level(role: str) -> int:
    """Get numeric level for a role."""
    return ROLE_HIERARCHY.get(role, 0)


def require_role(min_role: str):
    """Dependency factory that enforces minimum role level."""
    min_level = get_role_level(min_role)
    
    def checker(auth: AuthContext) -> AuthContext:
        user_level = get_role_level(auth.role)
        if user_level < min_level:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for this operation"
            )
        return auth
    
    return checker


def can_manage_member(actor_role: str, target_role: str) -> bool:
    """Check if actor can manage a member with the target role."""
    return get_role_level(actor_role) > get_role_level(target_role)
