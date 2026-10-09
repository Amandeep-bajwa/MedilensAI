from typing import Callable
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.errors import AppException
from app.models.entities import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and validates JWT Bearer token from request authorization header.
    Resolves the authenticated User entity from the database.
    """
    payload = decode_access_token(token)
    if not payload:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message="Could not validate credentials or token expired."
        )
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Token payload is invalid."
        )
        
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="User account does not exist."
        )
        
    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="INACTIVE_USER",
            message="Inactive user account."
        )
        
    return user

def require_role(*allowed_roles: str) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that current user role belongs to allowed_roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}."
            )
        return current_user
    return role_checker

# Predefined RBAC dependencies
require_admin = require_role("admin")
require_active_user = require_role("user", "admin")
