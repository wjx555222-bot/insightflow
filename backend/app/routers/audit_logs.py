"""Audit logs router for querying and creating audit log entries."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_role
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["audit_logs"])


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry (internal use)."""
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """List audit logs with optional filters. Admin only.

    Filters:
    - user_id: filter by the user who performed the action
    - action: filter by action type (e.g. "create", "update", "delete", "login")
    - entity_type: filter by the type of entity affected
    - date_from: only logs on or after this timestamp
    - date_to: only logs on or before this timestamp
    """
    query = db.query(AuditLog).options(joinedload(AuditLog.user))

    filters = []
    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if action is not None:
        filters.append(AuditLog.action == action)
    if entity_type is not None:
        filters.append(AuditLog.entity_type == entity_type)
    if date_from is not None:
        filters.append(AuditLog.timestamp >= date_from)
    if date_to is not None:
        filters.append(AuditLog.timestamp <= date_to)

    if filters:
        query = query.filter(and_(*filters))

    logs = (
        query
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for log in logs:
        user_email = log.user.email if log.user else None
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=user_email,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        ))

    return result


@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
def create_audit_log(
    payload: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create a new audit log entry.

    This endpoint is intended for internal use by other routers or admin
    tooling.  It validates that the referenced user exists.
    """
    # Validate the referenced user
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {payload.user_id} not found",
        )

    log_entry = AuditLog(
        user_id=payload.user_id,
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        details=payload.details,
        ip_address=payload.ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return AuditLogResponse(
        id=log_entry.id,
        user_id=log_entry.user_id,
        user_email=target_user.email,
        action=log_entry.action,
        entity_type=log_entry.entity_type,
        entity_id=log_entry.entity_id,
        details=log_entry.details,
        ip_address=log_entry.ip_address,
        timestamp=log_entry.timestamp,
    )
