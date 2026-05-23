"""
GrokDent FL — Clinic Settings Router
CRUD operations for the authenticated user's clinic profile.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.clinic import Clinic
from backend.models.user import User
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Clinics"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ClinicResponse(BaseModel):
    id: str
    name: str
    slug: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    timezone: Optional[str] = None
    services: Optional[List[str]] = None
    hours: Optional[Dict[str, Any]] = None
    insurance_accepted: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    grok_voice_id: Optional[str] = None
    welcome_message: Optional[str] = None
    spanish_enabled: Optional[bool] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ClinicUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    policies: Optional[str] = None


class HoursUpdate(BaseModel):
    hours: Dict[str, Any] = Field(..., description="Day → {open, close}")


class ServicesUpdate(BaseModel):
    services: List[str]


class InsuranceUpdate(BaseModel):
    insurance_accepted: List[str]


class VoiceSettingsUpdate(BaseModel):
    grok_voice_id: Optional[str] = None
    welcome_message: Optional[str] = None
    spanish_enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _get_clinic(db: Session, user: User) -> Clinic:
    clinic = db.query(Clinic).filter(Clinic.id == user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/", response_model=ClinicResponse)
async def get_clinic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's clinic profile."""
    clinic = _get_clinic(db, current_user)
    return ClinicResponse.model_validate(clinic)


@router.put("/", response_model=ClinicResponse)
async def update_clinic(
    body: ClinicUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update general clinic profile fields."""
    clinic = _get_clinic(db, current_user)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(clinic, key, value)

    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.put("/hours", response_model=ClinicResponse)
async def update_hours(
    body: HoursUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update clinic operating hours."""
    clinic = _get_clinic(db, current_user)
    clinic.hours = body.hours
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.put("/services", response_model=ClinicResponse)
async def update_services(
    body: ServicesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the list of services offered."""
    clinic = _get_clinic(db, current_user)
    clinic.services = body.services
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.put("/insurance", response_model=ClinicResponse)
async def update_insurance(
    body: InsuranceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the list of accepted insurance providers."""
    clinic = _get_clinic(db, current_user)
    clinic.insurance_accepted = body.insurance_accepted
    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)


@router.put("/voice-settings", response_model=ClinicResponse)
async def update_voice_settings(
    body: VoiceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update voice AI settings (voice ID, welcome message, Spanish toggle)."""
    clinic = _get_clinic(db, current_user)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(clinic, key, value)

    db.commit()
    db.refresh(clinic)
    return ClinicResponse.model_validate(clinic)
