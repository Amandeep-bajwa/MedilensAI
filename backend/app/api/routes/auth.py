from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.errors import AppException
from app.models.entities import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserSummary,
    PasswordChangeRequest
)
from app.api.deps import get_current_user
from app.services.audit import record_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with unique email validation and bcrypt hashing.
    Generates an immediate JWT access token upon successful registration.
    """
    normalized_email = payload.email.lower().strip()
    
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="EMAIL_ALREADY_REGISTERED",
            message="An account with this email address already exists."
        )
    
    assigned_role = payload.role if payload.role in ["user", "admin"] else "user"

    new_user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=get_password_hash(payload.password),
        role=assigned_role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Security Audit Trail
    record_audit_log(
        db=db,
        event_type="AUTH_REGISTER",
        result="Success",
        user_id=new_user.user_id,
        metadata_info={"email": normalized_email, "role": assigned_role}
    )

    access_token = create_access_token(
        subject=new_user.user_id,
        extra_claims={"role": new_user.role, "email": new_user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary.model_validate(new_user)
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token"
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Validates user credentials and issues a signed HMAC-SHA256 JWT access token.
    Records success and failure attempts in the audit trail.
    """
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        record_audit_log(
            db=db,
            event_type="AUTH_LOGIN",
            result="Failure",
            metadata_info={"attempted_email": normalized_email}
        )
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message="Incorrect email or password."
        )

    if not user.is_active:
        record_audit_log(
            db=db,
            event_type="AUTH_LOGIN",
            result="Failure",
            user_id=user.user_id,
            metadata_info={"reason": "account_deactivated"}
        )
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_DEACTIVATED",
            message="Your account has been deactivated. Please contact support."
        )

    record_audit_log(
        db=db,
        event_type="AUTH_LOGIN",
        result="Success",
        user_id=user.user_id,
        metadata_info={"email": user.email}
    )

    access_token = create_access_token(
        subject=user.user_id,
        extra_claims={"role": user.role, "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary.model_validate(user)
    )

@router.get(
    "/me",
    response_model=UserSummary,
    summary="Get current authenticated user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the decoded profile summary of the currently authenticated bearer.
    """
    return UserSummary.model_validate(current_user)

@router.post(
    "/change-password",
    summary="Update account password"
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows authenticated users to securely rotate their password.
    Enforces previous password verification and audit trail logging.
    """
    if not verify_password(payload.current_password, current_user.password_hash):
        record_audit_log(
            db=db,
            event_type="AUTH_PASSWORD_CHANGE",
            result="Failure",
            user_id=current_user.user_id,
            metadata_info={"reason": "wrong_current_password"}
        )
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_PASSWORD",
            message="Current password is incorrect."
        )

    if payload.current_password == payload.new_password:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PASSWORD_REUSE",
            message="New password cannot be the same as the current password."
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()

    record_audit_log(
        db=db,
        event_type="AUTH_PASSWORD_CHANGE",
        result="Success",
        user_id=current_user.user_id
    )

    return {"message": "Password updated successfully."}
