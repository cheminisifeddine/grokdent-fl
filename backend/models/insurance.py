"""
GrokDent FL - Insurance Model
Reference table of dental insurance providers available in Florida.
"""

import uuid
from sqlalchemy import Column, String, Boolean, Text
from backend.database import Base


class Insurance(Base):
    """
    Insurance provider reference — not clinic-specific.
    Tracks Florida-specific insurers plus national carriers.
    """

    __tablename__ = "insurance_providers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, unique=True, index=True)
    type = Column(
        String(20),
        nullable=False,
        doc="PPO | HMO | DHMO | Medicaid | Medicare",
    )
    florida_specific = Column(Boolean, default=False, doc="True if only in FL")
    phone = Column(String(20), nullable=True)
    website = Column(String(300), nullable=True)
    verification_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Insurance {self.name} ({self.type})>"
