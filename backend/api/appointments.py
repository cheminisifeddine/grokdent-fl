"""
GrokDent FL — Appointments Router
CRUD + availability lookup + voice-initiated booking for appointments.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.appointment import Appointment
from backend.models.clinic import Clinic
from backend.models.patient import Patient
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.services.calendar_service import calendar_service
from backend.services.notification_service import notification_service
from backend.services.encryption_service import encryption_service
from backend.utils.timezone import get_florida_now, format_appointment_time

_thread_pool = ThreadPoolExecutor(max_workers=4)


async def _run_sync(fn, *args, **kwargs):
    """Run a synchronous blocking function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_thread_pool, lambda: fn(*args, **kwargs))

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Appointments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AppointmentCreate(BaseModel):
    patient_id: Optional[str] = None
    appointment_datetime: datetime
    duration_minutes: int = 30
    service_type: str
    notes: Optional[str] = None
    created_via: str = "web_dashboard"


class AppointmentUpdate(BaseModel):
    appointment_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: Optional[str] = None
    appointment_datetime: datetime
    duration_minutes: int
    service_type: Optional[str] = None
    status: str
    notes: Optional[str] = None
    google_calendar_event_id: Optional[str] = None
    created_via: Optional[str] = None
    reminder_sent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AvailabilitySlot(BaseModel):
    start: str
    end: str


class AvailabilityResponse(BaseModel):
    date: str
    slots: List[AvailabilitySlot]
    clinic_name: str


class BookFromCallRequest(BaseModel):
    patient_name: str
    phone: str
    service: str
    preferred_time: datetime
    duration_minutes: int = 30
    language: str = "en"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List appointments for the user's clinic with optional filters."""
    query = db.query(Appointment).filter(Appointment.clinic_id == current_user.clinic_id)

    if date_from:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        query = query.filter(Appointment.appointment_datetime >= dt_from)
    if date_to:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        query = query.filter(Appointment.appointment_datetime <= dt_to)
    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(Appointment.appointment_datetime).all()
    return [AppointmentResponse.model_validate(a) for a in appointments]


@router.get("/today", response_model=List[AppointmentResponse])
async def todays_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List today's appointments in Eastern time."""
    now = get_florida_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.clinic_id == current_user.clinic_id,
            Appointment.appointment_datetime >= today_start,
            Appointment.appointment_datetime < today_end,
            Appointment.status != "cancelled",
        )
        .order_by(Appointment.appointment_datetime)
        .all()
    )
    return [AppointmentResponse.model_validate(a) for a in appointments]


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new appointment."""
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()

    # Validate patient belongs to same clinic if specified
    if body.patient_id:
        patient = db.query(Patient).filter(
            Patient.id == body.patient_id,
            Patient.clinic_id == current_user.clinic_id,
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found in this clinic")

    appointment = Appointment(
        clinic_id=current_user.clinic_id,
        patient_id=body.patient_id,
        appointment_datetime=body.appointment_datetime,
        duration_minutes=body.duration_minutes,
        service_type=body.service_type,
        notes=body.notes,
        created_via=body.created_via,
    )
    db.add(appointment)
    db.flush()

    # Sync to Google Calendar (run in thread pool to avoid blocking)
    if clinic:
        event_id = await _run_sync(
            calendar_service.create_event,
            clinic_name=clinic.name,
            patient_name="Patient",
            service=body.service_type,
            datetime_obj=body.appointment_datetime,
            duration=body.duration_minutes,
        )
        if event_id:
            appointment.google_calendar_event_id = event_id

    db.commit()
    db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    body: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an appointment's fields."""
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an appointment (soft-delete via status change)."""
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_user.clinic_id,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "cancelled"

    # Remove from Google Calendar (run in thread pool)
    if appointment.google_calendar_event_id:
        await _run_sync(
            calendar_service.delete_event,
            appointment.google_calendar_event_id,
        )
        appointment.google_calendar_event_id = None

    db.commit()
    return {"message": "Appointment cancelled", "id": appointment_id}


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return available 30-minute slots for a given date."""
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    clinic_hours = clinic.hours or {}

    # Get calendar-based availability
    slots = calendar_service.get_availability(date, clinic_hours)

    # Also exclude slots that already have appointments in our DB
    target_date = datetime.strptime(date, "%Y-%m-%d")
    day_start = target_date.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.clinic_id == current_user.clinic_id,
            Appointment.appointment_datetime >= day_start,
            Appointment.appointment_datetime < day_end,
            Appointment.status != "cancelled",
        )
        .all()
    )

    booked_times = set()
    for appt in existing:
        booked_times.add(appt.appointment_datetime.strftime("%H:%M"))

    available_slots = [s for s in slots if s["start"] not in booked_times]

    return AvailabilityResponse(
        date=date,
        slots=[AvailabilitySlot(**s) for s in available_slots],
        clinic_name=clinic.name,
    )


@router.post("/book-from-call", response_model=AppointmentResponse, status_code=201)
async def book_from_call(
    body: BookFromCallRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint for the voice handler to book an appointment on behalf of
    a caller.  Does not require JWT auth (called internally).

    Creates or finds the patient, then creates the appointment.
    """
    # Find clinic from context — use the first active clinic as fallback
    clinic = db.query(Clinic).filter(Clinic.is_active == True).first()
    if not clinic:
        raise HTTPException(status_code=500, detail="No active clinic found")

    # Try to find existing patient by name
    name_parts = body.patient_name.strip().rsplit(" ", 1)
    first_name = name_parts[0] if len(name_parts) > 1 else body.patient_name.strip()
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    patient = (
        db.query(Patient)
        .filter(
            Patient.clinic_id == clinic.id,
            Patient.first_name.ilike(f"%{first_name}%"),
        )
        .first()
    )

    if not patient:
        # Create new patient
        patient = Patient(
            clinic_id=clinic.id,
            first_name=first_name,
            last_name=last_name,
            phone_encrypted=encryption_service.encrypt(body.phone),
            preferred_language=body.language,
        )
        db.add(patient)
        db.flush()

    # Create appointment
    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        appointment_datetime=body.preferred_time,
        duration_minutes=body.duration_minutes,
        service_type=body.service,
        created_via="ai_voice",
    )
    db.add(appointment)

    # Sync to Google Calendar (run in thread pool)
    event_id = await _run_sync(
        calendar_service.create_event,
        clinic_name=clinic.name,
        patient_name=body.patient_name,
        service=body.service,
        datetime_obj=body.preferred_time,
        duration=body.duration_minutes,
    )
    if event_id:
        appointment.google_calendar_event_id = event_id

    db.commit()
    db.refresh(appointment)

    # Send confirmation SMS (run in thread pool)
    formatted_time = format_appointment_time(body.preferred_time)
    await _run_sync(
        notification_service.send_appointment_confirmation_sms,
        phone=body.phone,
        clinic_name=clinic.name,
        patient_name=body.patient_name,
        datetime_str=formatted_time,
        service=body.service,
        language=body.language,
    )

    logger.info(
        "Voice-booked appointment — patient=%s service=%s time=%s",
        body.patient_name, body.service, body.preferred_time,
    )

    return AppointmentResponse.model_validate(appointment)
