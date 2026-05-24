"""
GrokDent FL - Appointment Model
Tracks all patient appointments with status lifecycle and Google Calendar sync.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Appointment(Base):
    """
    Appointment entity.
    Status lifecycle: scheduled → confirmed → completed
                      scheduled → cancelled
                      scheduled → confirmed → no_show
    """

    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    appointment_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    service_type = Column(String(200), nullable=True, doc="e.g. cleaning, filling, root-canal")
    status = Column(
        String(20),
        default="scheduled",
        index=True,
        doc="scheduled | confirmed | cancelled | completed | no_show",
    )

    notes = Column(Text, nullable=True)
    google_calendar_event_id = Column(String(200), nullable=True)
    calcom_booking_id = Column(String(200), nullable=True)
    calendly_event_uri = Column(String(200), nullable=True)

    created_via = Column(
        String(20),
        default="manual",
        doc="ai_voice | web_dashboard | manual",
    )
    reminder_sent = Column(Boolean, default=False)

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment {self.id[:8]} — {self.service_type} @ {self.appointment_datetime}>"
