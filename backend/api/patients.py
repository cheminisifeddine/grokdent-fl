"""
GrokDent FL — Patients Router
Patient records management with secure decryption/encryption of PHI.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.patient import Patient
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Patients"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[str] = Field(None, description="YYYY-MM-DD")
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    preferred_language: str = "en"
    notes: Optional[str] = None

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    preferred_language: Optional[str] = None
    notes: Optional[str] = None

class PatientResponse(BaseModel):
    id: str
    clinic_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    preferred_language: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def decrypt_patient_model(p: Patient) -> PatientResponse:
    """Decrypt the encrypted fields of a Patient model for API response."""
    return PatientResponse(
        id=p.id,
        clinic_id=p.clinic_id,
        first_name=p.first_name,
        last_name=p.last_name,
        phone=encryption_service.decrypt(p.phone_encrypted) if p.phone_encrypted else None,
        email=encryption_service.decrypt(p.email_encrypted) if p.email_encrypted else None,
        dob=encryption_service.decrypt(p.dob_encrypted) if p.dob_encrypted else None,
        insurance_provider=p.insurance_provider,
        insurance_id=encryption_service.decrypt(p.insurance_id_encrypted) if p.insurance_id_encrypted else None,
        preferred_language=p.preferred_language or "en",
        notes=encryption_service.decrypt(p.notes_encrypted) if p.notes_encrypted else None,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all patients in the clinic, paginated."""
    patients = (
        db.query(Patient)
        .filter(Patient.clinic_id == current_user.clinic_id)
        .order_by(Patient.last_name, Patient.first_name)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [decrypt_patient_model(p) for p in patients]

@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search patients by first/last name, or scan decrypted phones/emails for a match.
    Since phone and email are encrypted, we decrypt results to filter them if a phone/email match is searched.
    For names, we can search directly.
    """
    # Name search
    name_query = db.query(Patient).filter(
        Patient.clinic_id == current_user.clinic_id,
        (Patient.first_name.ilike(f"%{q}%")) | (Patient.last_name.ilike(f"%{q}%"))
    ).all()
    
    results = [decrypt_patient_model(p) for p in name_query]
    
    # If no name results, or just to be thorough, scan all patients for encrypted phone/email matches
    # Since this is a specialized clinic dashboard, loading all patient lists is fast.
    if not results:
        all_patients = db.query(Patient).filter(Patient.clinic_id == current_user.clinic_id).all()
        for p in all_patients:
            dec_phone = encryption_service.decrypt(p.phone_encrypted) if p.phone_encrypted else ""
            dec_email = encryption_service.decrypt(p.email_encrypted) if p.email_encrypted else ""
            if q in dec_phone or q.lower() in dec_email.lower():
                results.append(decrypt_patient_model(p))
                
    return results

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific patient record, fully decrypted."""
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.clinic_id == current_user.clinic_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return decrypt_patient_model(patient)

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new patient record with encrypted PII."""
    patient = Patient(
        clinic_id=current_user.clinic_id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone_encrypted=encryption_service.encrypt(body.phone) if body.phone else None,
        email_encrypted=encryption_service.encrypt(body.email) if body.email else None,
        dob_encrypted=encryption_service.encrypt(body.dob) if body.dob else None,
        insurance_provider=body.insurance_provider,
        insurance_id_encrypted=encryption_service.encrypt(body.insurance_id) if body.insurance_id else None,
        preferred_language=body.preferred_language,
        notes_encrypted=encryption_service.encrypt(body.notes) if body.notes else None
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return decrypt_patient_model(patient)

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    body: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update patient fields securely."""
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.clinic_id == current_user.clinic_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = body.model_dump(exclude_unset=True)
    
    # Encrypt inputs if they are in update list
    if "first_name" in update_data:
        patient.first_name = update_data["first_name"]
    if "last_name" in update_data:
        patient.last_name = update_data["last_name"]
    if "phone" in update_data:
        patient.phone_encrypted = encryption_service.encrypt(update_data["phone"]) if update_data["phone"] else None
    if "email" in update_data:
        patient.email_encrypted = encryption_service.encrypt(update_data["email"]) if update_data["email"] else None
    if "dob" in update_data:
        patient.dob_encrypted = encryption_service.encrypt(update_data["dob"]) if update_data["dob"] else None
    if "insurance_provider" in update_data:
        patient.insurance_provider = update_data["insurance_provider"]
    if "insurance_id" in update_data:
        patient.insurance_id_encrypted = encryption_service.encrypt(update_data["insurance_id"]) if update_data["insurance_id"] else None
    if "preferred_language" in update_data:
        patient.preferred_language = update_data["preferred_language"]
    if "notes" in update_data:
        patient.notes_encrypted = encryption_service.encrypt(update_data["notes"]) if update_data["notes"] else None

    patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(patient)
    return decrypt_patient_model(patient)
