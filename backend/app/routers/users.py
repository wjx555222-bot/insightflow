"""Users router with admin-only user management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import hash_password
from app.utils.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])


def _get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Return a paginated list of all users. Admin only."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new user account. Admin only.

    Returns 409 if the email is already registered.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Resolve role
    if payload.role_id is not None:
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {payload.role_id} does not exist",
            )
    else:
        role = db.query(Role).filter(Role.name == "staff").first()
        if role is None:
            role = Role(name="staff")
            db.add(role)
            db.flush()

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

    log_action(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="user",
        entity_id=new_user.id,
        details=f"Created user {new_user.email}",
        ip_address=_get_client_ip(request),
    )

    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update an existing user's profile fields. Admin only.

    Returns 404 if the user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    if payload.email is not None:
        dup = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role_id is not None:
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {payload.role_id} does not exist",
            )
        user.role_id = role.id

    db.commit()
    db.refresh(user)

    log_action(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="user",
        entity_id=user.id,
        details=f"Updated user {user.email}",
        ip_address=_get_client_ip(request),
    )

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Soft-delete a user by setting is_active=False. Admin only.

    Returns 404 if the user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    user.is_active = False
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type="user",
        entity_id=user.id,
        details=f"Soft-deleted user {user.email}",
        ip_address=_get_client_ip(request),
    )

    return {"detail": f"User {user_id} has been deactivated"}
