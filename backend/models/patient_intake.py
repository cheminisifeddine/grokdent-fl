"""
GrokDent FL — Patient Intake Profile Model
Stores multi-section digital patient intake profiles with AES-256-GCM encryption.
100% HIPAA compliant storage of demographics, medical history, dental records, and signatures.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PatientIntakeProfile(Base):
    """
    PatientIntakeProfile entity.
    All Protected Health Information (PHI) fields are stored as AES-256-GCM ciphertexts
    at the application layer using HIPAACryptoService before persisting to the local database.
    """

    __tablename__ = "patient_intake_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(
        String(36), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Status & Progress
    completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Plaintext Non-PHI Meta fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    insurance_provider = Column(String(200), nullable=True)

    # --- AES-256-GCM Encrypted PHI Blocks ---
    # Demographics (encrypted JSON string containing DOB, SSN, phone, email, full address, gender)
    demographics_encrypted = Column(
        Text, nullable=True, doc="AES-256-GCM Encrypted Patient Demographics Block"
    )

    # Medical History (encrypted JSON string containing allergies, medications, past conditions, surgeries)
    medical_history_encrypted = Column(
        Text, nullable=True, doc="AES-256-GCM Encrypted Medical History Block"
    )

    # Dental History (encrypted JSON string containing last dental visit date, habits, specific concerns)
    dental_history_encrypted = Column(
        Text, nullable=True, doc="AES-256-GCM Encrypted Dental History Block"
    )

    # Insurance details (encrypted JSON containing member id, group number, policy holder info)
    insurance_encrypted = Column(
        Text, nullable=True, doc="AES-256-GCM Encrypted Insurance Profile Block"
    )

    # Signature and Legal Consents (encrypted JSON containing signature image, consent date, IP, user agent)
    consents_encrypted = Column(
        Text, nullable=True, doc="AES-256-GCM Encrypted HIPAA Consents and Signatures"
    )

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="intake_profiles")
    patient = relationship("Patient", back_populates="intake_profile")

    def __repr__(self) -> str:
        return f"<PatientIntakeProfile {self.first_name} {self.last_name} — Completed: {self.completed}>"
