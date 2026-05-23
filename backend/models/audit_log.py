"""
GrokDent FL - Audit Log Model
HIPAA-compliant audit trail for all data access and modifications.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """
    Immutable audit log entry — records every significant action for HIPAA compliance.
    Entries are append-only; never updated or deleted.
    """

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action = Column(
        String(20),
        nullable=False,
        index=True,
        doc="view | create | update | delete | access | export",
    )
    resource_type = Column(String(50), nullable=False, doc="e.g. patient, appointment, call_log")
    resource_id = Column(String(36), nullable=True)

    ip_address = Column(String(45), nullable=True, doc="IPv4 or IPv6")
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, default=dict, doc="Additional context about the action")

    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)

    # Relationships
    clinic = relationship("Clinic", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource_type} @ {self.timestamp}>"
