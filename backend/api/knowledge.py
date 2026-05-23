"""
GrokDent FL — Knowledge Base Router
Clinic-specific FAQ repository that Grok's voice agent references during patient calls.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.knowledge_base import KnowledgeBase
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.utils.florida_data import SAMPLE_KNOWLEDGE_BASE

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Knowledge Base"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class KBEntryCreate(BaseModel):
    category: str = Field(..., description="general|services|insurance|pricing|hours|location|emergency|policies")
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=10)
    answer_spanish: Optional[str] = None
    priority: int = 0
    is_active: bool = True

class KBEntryUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    answer_spanish: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class KBEntryResponse(BaseModel):
    id: str
    clinic_id: str
    category: str
    question: str
    answer: str
    answer_spanish: Optional[str] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[KBEntryResponse])
async def list_kb_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all active/inactive knowledge base entries for the clinic."""
    entries = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.clinic_id == current_user.clinic_id)
        .order_by(KnowledgeBase.category, KnowledgeBase.priority.desc(), KnowledgeBase.question)
        .all()
    )
    return [KBEntryResponse.model_validate(e) for e in entries]

@router.get("/category/{category}", response_model=List[KBEntryResponse])
async def list_kb_by_category(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve knowledge base entries by category."""
    entries = (
        db.query(KnowledgeBase)
        .filter(
            KnowledgeBase.clinic_id == current_user.clinic_id,
            KnowledgeBase.category == category
        )
        .order_by(KnowledgeBase.priority.desc(), KnowledgeBase.question)
        .all()
    )
    return [KBEntryResponse.model_validate(e) for e in entries]

@router.post("/", response_model=KBEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_kb_entry(
    body: KBEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new knowledge base entry."""
    entry = KnowledgeBase(
        clinic_id=current_user.clinic_id,
        category=body.category,
        question=body.question,
        answer=body.answer,
        answer_spanish=body.answer_spanish,
        priority=body.priority,
        is_active=body.is_active
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return KBEntryResponse.model_validate(entry)

@router.put("/{entry_id}", response_model=KBEntryResponse)
async def update_kb_entry(
    entry_id: str,
    body: KBEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing knowledge base FAQ entry."""
    entry = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == entry_id, KnowledgeBase.clinic_id == current_user.clinic_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)

    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return KBEntryResponse.model_validate(entry)

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge base entry."""
    entry = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == entry_id, KnowledgeBase.clinic_id == current_user.clinic_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    db.delete(entry)
    db.commit()
    return None

@router.post("/seed-defaults", response_model=List[KBEntryResponse], status_code=status.HTTP_201_CREATED)
async def seed_defaults(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Seed the clinic's knowledge base with standard, Florida-tailored dental FAQ questions."""
    clinic_id = current_user.clinic_id

    # Check if we already have entries to prevent massive duplicates
    existing_count = db.query(KnowledgeBase).filter(KnowledgeBase.clinic_id == clinic_id).count()
    if existing_count > 0:
        raise HTTPException(status_code=400, detail="Knowledge base is not empty. Cannot seed defaults.")

    new_entries = []
    # SUNSHINE_SMILES_KB contains pre-formulated dental QA dicts
    for item in SAMPLE_KNOWLEDGE_BASE:
        entry = KnowledgeBase(
            clinic_id=clinic_id,
            category=item.get("category", "general"),
            question=item.get("question"),
            answer=item.get("answer"),
            answer_spanish=item.get("answer_spanish"),
            priority=item.get("priority", 0),
            is_active=True
        )
        db.add(entry)
        new_entries.append(entry)

    db.commit()
    for e in new_entries:
        db.refresh(e)

    logger.info("Seeded %d FAQ entries for clinic %s", len(new_entries), clinic_id)
    return [KBEntryResponse.model_validate(e) for e in new_entries]
