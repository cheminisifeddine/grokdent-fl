"""
GrokDent FL - User Model
Dashboard users (admin, manager, staff) linked to a clinic tenant.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    User entity — each user belongs to exactly one clinic.
    Roles: admin (full access), manager (most access), staff (read-mostly).
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )

    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), default="staff", doc="admin | manager | staff")

    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
