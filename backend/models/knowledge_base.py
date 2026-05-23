"""
GrokDent FL - Knowledge Base Model
Clinic-specific FAQ entries the AI receptionist uses to answer patient questions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeBase(Base):
    """
    Knowledge base entry — question/answer pair organized by category.
    Higher priority entries are preferred when multiple answers match.
    """

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(
        String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category = Column(
        String(30),
        nullable=False,
        index=True,
        doc="general | services | insurance | pricing | hours | location | emergency | policies",
    )
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answer_spanish = Column(Text, nullable=True, doc="Spanish translation of the answer")

    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0, doc="Higher = shown first")

    # Meta
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="knowledge_entries")

    def __repr__(self) -> str:
        return f"<KnowledgeBase [{self.category}] {self.question[:40]}>"
