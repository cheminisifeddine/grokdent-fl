"""
GrokDent FL - Call Log Model
Records every inbound/outbound call with encrypted transcript, sentiment, and action log.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CallLog(Base):
    """
    Call log entity — one row per Twilio call.
    Transcript and recording URL are encrypted at rest for HIPAA compliance.
    """

    __tablename__ = "call_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Twilio metadata
    twilio_call_sid = Column(String(64), unique=True, nullable=False, index=True)
    direction = Column(String(10), default="inbound", doc="inbound | outbound")
    caller_number = Column(String(20), nullable=True)
    called_number = Column(String(20), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(
        String(20),
        default="completed",
        doc="completed | missed | voicemail | transferred",
    )

    # Conversation content (encrypted)
    transcript_encrypted = Column(Text, nullable=True, doc="Encrypted full transcript")
    summary = Column(Text, nullable=True, doc="AI-generated call summary")
    sentiment = Column(String(10), default="neutral", doc="positive | neutral | negative")

    # Language & actions
    language = Column(String(2), default="en", doc="en | es")
    actions_taken = Column(JSON, default=list, doc="List of actions performed during call")
    recording_url_encrypted = Column(Text, nullable=True, doc="Encrypted recording URL")

    # Flags
    is_emergency = Column(Boolean, default=False)

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="call_logs")
    patient = relationship("Patient", back_populates="call_logs")

    def __repr__(self) -> str:
        return f"<CallLog {self.twilio_call_sid} ({self.direction})>"
