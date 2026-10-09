from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.entities import AuditLog

def record_audit_log(
    db: Session,
    event_type: str,
    result: str,
    user_id: Optional[str] = None,
    metadata_info: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Persists an auditable security event into the audit_logs table.
    Enforces compliance with healthcare data auditability standards.
    """
    log_entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        result=result,
        metadata_info=metadata_info or {}
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
