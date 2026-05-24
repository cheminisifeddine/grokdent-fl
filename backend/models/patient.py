"""
GrokDent FL - Patient Model
Stores patient data with HIPAA-compliant field-level encryption for PHI.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    """
    Patient entity.
    Sensitive fields (phone, email, dob, insurance_id, notes) are stored encrypted
    at the application layer via EncryptionService before persisting.
    """

    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Encrypted PHI fields — stored as Fernet ciphertext
    phone_encrypted = Column(Text, nullable=True, doc="Encrypted phone number")
    email_encrypted = Column(Text, nullable=True, doc="Encrypted email address")
    dob_encrypted = Column(Text, nullable=True, doc="Encrypted date of birth")

    # Insurance
    insurance_provider = Column(String(200), nullable=True)
    insurance_id_encrypted = Column(Text, nullable=True, doc="Encrypted insurance member ID")

    # Preferences
    preferred_language = Column(String(2), default="en", doc="en | es")

    # Clinical notes (encrypted)
    notes_encrypted = Column(Text, nullable=True, doc="Encrypted clinical notes")

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="patient")
    intake_profile = relationship("PatientIntakeProfile", back_populates="patient", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Patient {self.first_name} {self.last_name}>"
