"""Authentication router with login, register, and current-user endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    hash_password,
)
from app.utils.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from the request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate a user with email and password, returning a JWT token.

    Returns 401 if credentials are invalid or the account is deactivated.
    """
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    log_action(
        db,
        user_id=user.id,
        action="login",
        entity_type="auth",
        details=f"User {user.email} logged in",
        ip_address=_get_client_ip(request),
    )

    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=TokenResponse)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user account.

    The first registered user is automatically promoted to admin regardless
    of the requested role.  Subsequent registrations default to the requested
    role (or 'staff' if none specified).  An existing admin can also use this
    endpoint to create additional accounts.

    Returns 409 if the email address is already registered.
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Determine the role to assign
    user_count = db.query(User).count()
    role_name = payload.role if user_count > 0 else "admin"

    # Get or create the role
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.flush()

    # Create user
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id)})

    log_action(
        db,
        user_id=new_user.id,
        action="register",
        entity_type="user",
        entity_id=new_user.id,
        details=f"New user registered: {new_user.email} with role {role_name}",
        ip_address=_get_client_ip(request),
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile information."""
    return current_user
