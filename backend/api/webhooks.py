"""
GrokDent FL — Twilio Webhook Router
Handle real-time Twilio voice calls, SMS text inquiries, status callbacks, and TwiML generators.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.call_log import CallLog
from backend.voice.voice_handler import VoiceHandler

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Twilio Webhooks"])

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/voice/incoming")
async def incoming_call(request: Request, db: Session = Depends(get_db)):
    """
    Twilio voice webhook for incoming phone calls.
    Returns initial TwiML greeting with <Gather> for speech.
    """
    form_data = await request.form()
    request_dict = dict(form_data)
    
    twiml_response = VoiceHandler.handle_incoming_call(request_dict, db)
    
    return Response(
        content=twiml_response,
        media_type="application/xml"
    )

@router.post("/voice/gather")
async def voice_gather(request: Request, db: Session = Depends(get_db)):
    """
    Twilio action callback for speech gather.
    Processes speech result through Grok agent reasoning and returns the next TwiML dialog state.
    """
    form_data = await request.form()
    request_dict = dict(form_data)
    
    speech_result = request_dict.get("SpeechResult", "")
    call_sid = request_dict.get("CallSid", "unknown")
    
    # Process speech utterance
    twiml_response = await VoiceHandler.process_speech_input(
        speech_text=speech_result,
        call_sid=call_sid,
        db=db
    )
    
    return Response(
        content=twiml_response,
        media_type="application/xml"
    )

@router.post("/voice/status")
async def voice_status(request: Request, db: Session = Depends(get_db)):
    """
    Twilio status callback webhook.
    Fired when call ends. Persists final call logs, sentiment, and transcripts to database.
    """
    form_data = await request.form()
    request_dict = dict(form_data)
    
    call_sid = request_dict.get("CallSid")
    call_status = request_dict.get("CallStatus")
    duration = request_dict.get("CallDuration")
    caller = request_dict.get("From", "")
    called = request_dict.get("To", "")
    
    logger.info("Call status callback — SID=%s status=%s duration=%s", call_sid, call_status, duration)
    
    if call_status in ("completed", "busy", "failed", "no-answer"):
        # Save transcript & call log to database
        call_log = VoiceHandler.end_call(call_sid, db)
        if call_log:
            # Update caller details from Twilio payload
            call_log.caller_number = caller
            call_log.called_number = called
            if duration:
                call_log.duration_seconds = int(duration)
            call_log.status = call_status
            db.commit()
            
    return Response(status_code=200)

@router.post("/sms/incoming")
async def incoming_sms(request: Request):
    """
    Twilio SMS webhook for text conversations.
    Provides simple automated dental scheduling response with clinic information.
    """
    form_data = await request.form()
    request_dict = dict(form_data)
    
    body = request_dict.get("Body", "").strip()
    sender = request_dict.get("From", "")
    
    logger.info("Incoming SMS from %s: %s", sender, body)
    
    # Standard helpful SMS response
    sms_reply = (
        "Hi there! This is the GrokDent FL AI Assistant. 🦷\n\n"
        "I can help you book, cancel, or reschedule appointments, and answer any "
        "questions you might have about our dental practices. Please call this number "
        "to speak with me directly, or visit our online clinic dashboard to manage your details. "
        "Have a wonderful day!"
    )
    
    twiml_response = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Message>{sms_reply}</Message>'
        '</Response>'
    )
    
    return Response(
        content=twiml_response,
        media_type="application/xml"
    )
