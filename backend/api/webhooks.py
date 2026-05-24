"""
GrokDent FL — Twilio Webhook Router
Handle real-time Twilio voice calls, SMS text inquiries, status callbacks, and TwiML generators.
"""

import hashlib
import hmac
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.call_log import CallLog
from backend.voice.voice_handler import VoiceHandler

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Twilio Webhooks"])


def _verify_twilio_signature(request: Request, form_data: dict) -> bool:
    """Validate Twilio request using X-Twilio-Signature."""
    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    auth_token = settings.TWILIO_AUTH_TOKEN
    if not auth_token or auth_token == "placeholder":
        logger.warning("TWILIO_AUTH_TOKEN not configured — skipping signature verification")
        return True
    url = str(request.url)
    expected = form_data.get("expected", "")
    params = {k: v for k, v in form_data.items() if k != "expected"}
    params_str = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    sig_str = url + params_str
    expected_sig = hmac.new(
        auth_token.encode(), sig_str.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, twilio_signature)


async def _parse_form(request: Request):
    form_data = await request.form()
    return dict(form_data)


@router.post("/voice/incoming")
async def incoming_call(request: Request, db: Session = Depends(get_db)):
    form_data = await _parse_form(request)
    request_dict = dict(form_data)

    try:
        twiml_response = VoiceHandler.handle_incoming_call(request_dict, db)
    except Exception as exc:
        logger.error("Incoming call handler failed: %s", exc)
        twiml_response = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Say>We are experiencing a system issue. Please try again later. Goodbye!</Say>"
            "</Response>"
        )

    return Response(content=twiml_response, media_type="application/xml")


@router.post("/voice/gather")
async def voice_gather(request: Request, db: Session = Depends(get_db)):
    form_data = await _parse_form(request)
    request_dict = dict(form_data)

    speech_result = request_dict.get("SpeechResult", "")
    call_sid = request_dict.get("CallSid", "unknown")

    try:
        twiml_response = await VoiceHandler.process_speech_input(
            speech_text=speech_result,
            call_sid=call_sid,
            db=db,
        )
    except Exception as exc:
        logger.error("Speech processing failed for SID=%s: %s", call_sid, exc)
        twiml_response = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Say>I apologize, but I am having trouble processing your request. "
            "Let me transfer you to our team.</Say>"
            "<Dial>+18885551234</Dial>"
            "</Response>"
        )

    return Response(content=twiml_response, media_type="application/xml")


@router.post("/voice/status")
async def voice_status(request: Request, db: Session = Depends(get_db)):
    form_data = await _parse_form(request)
    request_dict = dict(form_data)

    call_sid = request_dict.get("CallSid")
    call_status = request_dict.get("CallStatus")
    duration = request_dict.get("CallDuration")
    caller = request_dict.get("From", "")
    called = request_dict.get("To", "")

    logger.info("Call status callback — SID=%s status=%s duration=%s", call_sid, call_status, duration)

    if call_status in ("completed", "busy", "failed", "no-answer"):
        try:
            call_log = VoiceHandler.end_call(call_sid, db)
            if call_log:
                call_log.caller_number = caller
                call_log.called_number = called
                if duration:
                    call_log.duration_seconds = int(duration)
                call_log.status = call_status
                db.commit()
        except Exception as exc:
            logger.error("Failed to process end_call for SID=%s: %s", call_sid, exc)

    return Response(status_code=200)


@router.post("/sms/incoming")
async def incoming_sms(request: Request):
    form_data = await _parse_form(request)
    request_dict = dict(form_data)

    body = request_dict.get("Body", "").strip()
    sender = request_dict.get("From", "")

    logger.info("Incoming SMS from %s: %s", sender, body)

    sms_reply = (
        "Hi there! This is the GrokDent FL AI Assistant.\n\n"
        "I can help you book, cancel, or reschedule appointments, and answer any "
        "questions you might have about our dental practices. Please call this number "
        "to speak with me directly, or visit our online clinic dashboard to manage your details. "
        "Have a wonderful day!"
    )

    twiml_response = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{sms_reply}</Message>"
        "</Response>"
    )

    return Response(content=twiml_response, media_type="application/xml")
