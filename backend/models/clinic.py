"""
GrokDent FL - Clinic Model
Represents a dental clinic with all configuration, services, and subscription info.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Text, DateTime, JSON, Enum as SAEnum
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Clinic(Base):
    """Dental clinic entity — the core tenant in the multi-clinic SaaS."""

    __tablename__ = "clinics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)

    # Location
    address = Column(String(300), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), default="FL")
    zip_code = Column(String(10), nullable=True)
    timezone = Column(String(50), default="US/Eastern")

    # Services & Operations
    services = Column(JSON, default=list, doc="List of services offered")
    hours = Column(JSON, default=dict, doc="Dict of day -> {open, close}")
    insurance_accepted = Column(JSON, default=list, doc="List of accepted insurance providers")

    # Emergency
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    # Voice AI
    grok_voice_id = Column(String(50), default="Aria", doc="TTS voice selection")
    xai_key = Column(String(200), nullable=True, doc="Per-clinic xAI API key")

    # Twilio
    twilio_phone_number = Column(String(20), nullable=True)

    # Stripe / Billing
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    subscription_plan = Column(
        String(20), default="starter",
        doc="starter | professional | enterprise",
    )
    subscription_status = Column(
        String(20), default="trial",
        doc="active | inactive | trial",
    )

    # Policies & Messaging
    policies = Column(Text, nullable=True, doc="Cancellation, late, payment policies")
    instructions = Column(Text, nullable=True, doc="AI voice system instructions / persona prompt")
    welcome_message = Column(
        Text,
        nullable=True,
        default="Welcome to our dental office! How can I help you today?",
    )
    spanish_enabled = Column(Boolean, default=True, doc="Enable Spanish language support")

    # Meta
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    users = relationship("User", back_populates="clinic", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="clinic", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="clinic", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="clinic", cascade="all, delete-orphan")
    knowledge_entries = relationship("KnowledgeBase", back_populates="clinic", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="clinic", cascade="all, delete-orphan")
    intake_profiles = relationship("PatientIntakeProfile", back_populates="clinic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Clinic {self.name} ({self.slug})>"
