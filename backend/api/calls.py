"""
GrokDent FL — Call Logs Router
Retrieve and analyze patient call records, decrypting PHI call transcripts and recording URLs.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.call_log import CallLog
from backend.models.patient import Patient
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Calls"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class PatientBrief(BaseModel):
    id: str
    first_name: str
    last_name: str

class CallLogResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: Optional[str] = None
    patient: Optional[PatientBrief] = None
    twilio_call_sid: str
    direction: str
    caller_number: str
    called_number: str
    duration_seconds: int
    status: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    actions_taken: Optional[List[str]] = None
    recording_url: Optional[str] = None
    is_emergency: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class CallStatsResponse(BaseModel):
    total_calls: int
    avg_duration_seconds: float
    sentiment_breakdown: Dict[str, int]
    language_breakdown: Dict[str, int]
    emergency_count: int

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def decrypt_call_log(log: CallLog) -> CallLogResponse:
    """Helper to decrypt sensitive call fields (transcript, recording URL) for response."""
    patient_brief = None
    if log.patient:
        patient_brief = PatientBrief(
            id=log.patient.id,
            first_name=log.patient.first_name,
            last_name=log.patient.last_name
        )

    return CallLogResponse(
        id=log.id,
        clinic_id=log.clinic_id,
        patient_id=log.patient_id,
        patient=patient_brief,
        twilio_call_sid=log.twilio_call_sid,
        direction=log.direction,
        caller_number=log.caller_number,
        called_number=log.called_number,
        duration_seconds=log.duration_seconds or 0,
        status=log.status or "completed",
        transcript=encryption_service.decrypt(log.transcript_encrypted) if log.transcript_encrypted else None,
        summary=log.summary,
        sentiment=log.sentiment or "neutral",
        language=log.language or "en",
        actions_taken=log.actions_taken or [],
        recording_url=encryption_service.decrypt(log.recording_url_encrypted) if log.recording_url_encrypted else None,
        is_emergency=log.is_emergency or False,
        created_at=log.created_at
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[CallLogResponse])
async def list_calls(
    direction: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    is_emergency: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve call logs for the user's clinic with filters, paginated."""
    query = db.query(CallLog).filter(CallLog.clinic_id == current_user.clinic_id)

    if direction:
        query = query.filter(CallLog.direction == direction)
    if sentiment:
        query = query.filter(CallLog.sentiment == sentiment)
    if language:
        query = query.filter(CallLog.language == language)
    if is_emergency is not None:
        query = query.filter(CallLog.is_emergency == is_emergency)

    logs = query.order_by(CallLog.created_at.desc()).offset(skip).limit(limit).all()
    return [decrypt_call_log(log) for log in logs]

@router.get("/recent", response_model=List[CallLogResponse])
async def get_recent_calls(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the last 10 calls for the dashboard feed."""
    logs = (
        db.query(CallLog)
        .filter(CallLog.clinic_id == current_user.clinic_id)
        .order_by(CallLog.created_at.desc())
        .limit(10)
        .all()
    )
    return [decrypt_call_log(log) for log in logs]

@router.get("/stats", response_model=CallStatsResponse)
async def get_call_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch call log statistics for reports."""
    clinic_id = current_user.clinic_id

    total_calls = db.query(CallLog).filter(CallLog.clinic_id == clinic_id).count()
    
    avg_duration = db.query(func.avg(CallLog.duration_seconds)).filter(CallLog.clinic_id == clinic_id).scalar() or 0.0

    sentiment_counts = (
        db.query(CallLog.sentiment, func.count(CallLog.id))
        .filter(CallLog.clinic_id == clinic_id)
        .group_by(CallLog.sentiment)
        .all()
    )
    sentiment_breakdown = {s or "neutral": count for s, count in sentiment_counts}

    language_counts = (
        db.query(CallLog.language, func.count(CallLog.id))
        .filter(CallLog.clinic_id == clinic_id)
        .group_by(CallLog.language)
        .all()
    )
    language_breakdown = {l or "en": count for l, count in language_counts}

    emergency_count = db.query(CallLog).filter(CallLog.clinic_id == clinic_id, CallLog.is_emergency == True).count()

    return CallStatsResponse(
        total_calls=total_calls,
        avg_duration_seconds=float(avg_duration),
        sentiment_breakdown=sentiment_breakdown,
        language_breakdown=language_breakdown,
        emergency_count=emergency_count
    )

@router.get("/{call_id}", response_model=CallLogResponse)
async def get_call_details(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific call log by ID, with fully decrypted conversation transcript."""
    log = (
        db.query(CallLog)
        .filter(CallLog.id == call_id, CallLog.clinic_id == current_user.clinic_id)
        .first()
    )
    if not log:
        raise HTTPException(status_code=404, detail="Call record not found")

    return decrypt_call_log(log)
