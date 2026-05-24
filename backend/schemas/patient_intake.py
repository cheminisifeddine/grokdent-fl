"""
GrokDent FL — Patient Intake Pydantic Schemas & HIPAA Validation Framework
Defines strict validation rules and automatic block-level AES-256-GCM encryption/decryption.
"""

import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.models.patient_intake import PatientIntakeProfile
from backend.services.hipaa_crypto import hipaa_crypto


# ---------------------------------------------------------------------------
# Section 1: Demographics Schema
# ---------------------------------------------------------------------------
class IntakeDemographics(BaseModel):
    dob: str = Field(..., description="YYYY-MM-DD", pattern=r"^\d{4}-\d{2}-\d{2}$")
    ssn: str = Field(..., description="Last 4 digits or full SSN", min_length=4, max_length=11)
    gender: str = Field(..., description="Male | Female | Other")
    phone: str = Field(..., description="Contact phone number")
    email: str = Field(..., description="Primary email address", pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    address_street: str = Field(..., min_length=1)
    address_city: str = Field(..., min_length=1)
    address_state: str = Field(..., min_length=2, max_length=2)
    address_zip: str = Field(..., min_length=5, max_length=10)


# ---------------------------------------------------------------------------
# Section 2: Medical History Schema
# ---------------------------------------------------------------------------
class IntakeMedicalHistory(BaseModel):
    allergies: str = Field(default="None reported", description="Allergies (e.g. Penicillin, Latex)")
    current_medications: str = Field(default="None", description="Currently taken prescription or OTC drugs")
    medical_conditions: str = Field(default="None", description="Pre-existing conditions (e.g. Asthma, Diabetes)")
    surgical_history: str = Field(default="None", description="Details of previous surgical operations")


# ---------------------------------------------------------------------------
# Section 3: Dental History Schema
# ---------------------------------------------------------------------------
class IntakeDentalHistory(BaseModel):
    last_visit_date: Optional[str] = Field(default=None, description="Rough date or YYYY-MM-DD of last cleaning")
    brush_floss_frequency: str = Field(..., description="Daily dental hygiene habits")
    specific_concerns: str = Field(default="None", description="Current dental pain or issues (e.g. bleeding gums)")


# ---------------------------------------------------------------------------
# Section 4: Insurance Details Schema
# ---------------------------------------------------------------------------
class IntakeInsurance(BaseModel):
    policy_holder_name: str = Field(..., description="Full name of primary policy holder")
    policy_holder_dob: str = Field(..., description="DOB of policy holder", pattern=r"^\d{4}-\d{2}-\d{2}$")
    member_id: str = Field(..., min_length=1, description="Insurance member ID")
    group_number: Optional[str] = Field(default=None, description="Insurance group number")


# ---------------------------------------------------------------------------
# Section 5: Signature & Legal Consent Schema
# ---------------------------------------------------------------------------
class IntakeConsents(BaseModel):
    hipaa_consent: bool = Field(..., description="Explicit acknowledgment of HIPAA privacy policies")
    financial_responsibility: bool = Field(..., description="Agreement to pay for co-pays or uncovered services")
    signature_name: str = Field(..., description="Legal name signed electronically")
    signature_date: str = Field(..., description="YYYY-MM-DD date of signing", pattern=r"^\d{4}-\d{2}-\d{2}$")
    signature_image_base64: Optional[str] = Field(None, description="Base64 png/jpeg of electronic signature")


# ---------------------------------------------------------------------------
# Consolidated Intake Creation Schema
# ---------------------------------------------------------------------------
class PatientIntakeCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    insurance_provider: Optional[str] = Field(None, max_length=200)

    demographics: IntakeDemographics
    medical_history: IntakeMedicalHistory
    dental_history: IntakeDentalHistory
    insurance: IntakeInsurance
    consents: IntakeConsents


# ---------------------------------------------------------------------------
# Complete Intake Response (Fully Decrypted view)
# ---------------------------------------------------------------------------
class PatientIntakeResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: Optional[str] = None
    completed: bool
    completed_at: Optional[datetime] = None

    first_name: str
    last_name: str
    insurance_provider: Optional[str] = None

    # Fully Decrypted Data structures
    demographics: IntakeDemographics
    medical_history: IntakeMedicalHistory
    dental_history: IntakeDentalHistory
    insurance: IntakeInsurance
    consents: IntakeConsents

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Cryptographic Framework Utilities (AES-256-GCM + Associated Data)
# ---------------------------------------------------------------------------
def encrypt_intake(
    body: PatientIntakeCreate,
    clinic_id: str,
    patient_id: Optional[str] = None
) -> PatientIntakeProfile:
    """
    Translates cleartext Pydantic schemas into an encrypted database model PatientIntakeProfile.
    
    Uses AES-256-GCM. The 'clinic_id' is passed as Associated Data (AD) to prevent cross-clinic
    swap/substitution attacks (guaranteeing that ciphertexts cannot be imported or read in other clinics).
    """
    # 1. Serialize sub-sections into JSON strings
    demo_json = body.demographics.model_dump_json()
    med_json = body.medical_history.model_dump_json()
    dent_json = body.dental_history.model_dump_json()
    ins_json = body.insurance.model_dump_json()
    consent_json = body.consents.model_dump_json()

    # 2. Encrypt blocks using clinic_id as Associated Data (AD)
    demo_encrypted = hipaa_crypto.encrypt(demo_json, associated_data=clinic_id)
    med_encrypted = hipaa_crypto.encrypt(med_json, associated_data=clinic_id)
    dent_encrypted = hipaa_crypto.encrypt(dent_json, associated_data=clinic_id)
    ins_encrypted = hipaa_crypto.encrypt(ins_json, associated_data=clinic_id)
    consent_encrypted = hipaa_crypto.encrypt(consent_json, associated_data=clinic_id)

    # 3. Instantiate DB model
    return PatientIntakeProfile(
        clinic_id=clinic_id,
        patient_id=patient_id,
        completed=True,  # Completed upon full structure submission
        completed_at=datetime.utcnow(),
        first_name=body.first_name,
        last_name=body.last_name,
        insurance_provider=body.insurance_provider,
        demographics_encrypted=demo_encrypted,
        medical_history_encrypted=med_encrypted,
        dental_history_encrypted=dent_encrypted,
        insurance_encrypted=ins_encrypted,
        consents_encrypted=consent_encrypted
    )


def decrypt_intake(profile: PatientIntakeProfile) -> PatientIntakeResponse:
    """
    Decrypts database PatientIntakeProfile model into a cleartext, structured PatientIntakeResponse.
    
    Verifies the AES-256-GCM tag using the clinic_id as Associated Data.
    Fails loudly if the cryptographic integrity has been compromised or key is rotated incorrectly.
    """
    clinic_id = profile.clinic_id

    # 1. Decrypt blocks
    demo_json = hipaa_crypto.decrypt(profile.demographics_encrypted, associated_data=clinic_id)
    med_json = hipaa_crypto.decrypt(profile.medical_history_encrypted, associated_data=clinic_id)
    dent_json = hipaa_crypto.decrypt(profile.dental_history_encrypted, associated_data=clinic_id)
    ins_json = hipaa_crypto.decrypt(profile.insurance_encrypted, associated_data=clinic_id)
    consent_json = hipaa_crypto.decrypt(profile.consents_encrypted, associated_data=clinic_id)

    # 2. Reconstruct sub-models
    demo_data = IntakeDemographics.model_validate_json(demo_json)
    med_data = IntakeMedicalHistory.model_validate_json(med_json)
    dent_data = IntakeDentalHistory.model_validate_json(dent_json)
    ins_data = IntakeInsurance.model_validate_json(ins_json)
    consent_data = IntakeConsents.model_validate_json(consent_json)

    # 3. Assemble response model
    return PatientIntakeResponse(
        id=profile.id,
        clinic_id=profile.clinic_id,
        patient_id=profile.patient_id,
        completed=profile.completed,
        completed_at=profile.completed_at,
        first_name=profile.first_name,
        last_name=profile.last_name,
        insurance_provider=profile.insurance_provider,
        demographics=demo_data,
        medical_history=med_data,
        dental_history=dent_data,
        insurance=ins_data,
        consents=consent_data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )
