from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry.

    This utility is intended to be imported and called by routers whenever
    a state-changing action occurs (create, update, delete, login, etc.).

    Parameters
    ----------
    db : Session
        Active SQLAlchemy database session.
    user_id : int
        ID of the user performing the action.
    action : str
        Human-readable action name (e.g. "create", "update", "delete", "login").
    entity_type : str
        The type of entity affected (e.g. "order", "customer", "user").
    entity_id : int, optional
        ID of the affected entity, if applicable.
    details : str, optional
        Additional context or metadata about the action.
    ip_address : str, optional
        IP address of the requesting client.

    Returns
    -------
    AuditLog
        The newly created and persisted audit log record.
    """
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
