"""
GrokDent FL — Voice Handler
Bridges Twilio phone calls ↔ ConversationManager ↔ Grok AI.
Generates TwiML XML responses for call flow control.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.clinic import Clinic
from backend.models.call_log import CallLog
from backend.services.encryption_service import encryption_service
from backend.services.emergency_service import emergency_service
from backend.voice.conversation_manager import ConversationManager
from backend.voice.grok_client import GrokVoiceClient
from backend.voice.language_router import LanguageRouter

logger = logging.getLogger(__name__)


def _twiml_say_gather(text: str, language: str = "en") -> str:
    """
    Build a TwiML ``<Response>`` with ``<Say>`` inside ``<Gather>``.

    Uses Google voices for more natural TTS on Twilio.
    """
    voice = "Polly.Joanna" if language == "en" else "Polly.Lupe"
    lang_code = "en-US" if language == "en" else "es-US"

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Gather input="speech" speechTimeout="auto" language="{lang_code}" '
        f'action="/api/v1/webhooks/voice/gather" method="POST">'
        f'<Say voice="{voice}">{_escape_xml(text)}</Say>'
        "</Gather>"
        f'<Say voice="{voice}">I didn\'t catch that. Goodbye!</Say>'
        "</Response>"
    )


def _twiml_say(text: str, language: str = "en") -> str:
    """Build a TwiML ``<Response>`` with a simple ``<Say>``."""
    voice = "Polly.Joanna" if language == "en" else "Polly.Lupe"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{voice}">{_escape_xml(text)}</Say>'
        "</Response>"
    )


def _twiml_transfer(text: str, phone: str, language: str = "en") -> str:
    """Build TwiML that says a message then dials a number."""
    voice = "Polly.Joanna" if language == "en" else "Polly.Lupe"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{voice}">{_escape_xml(text)}</Say>'
        f"<Dial>{phone}</Dial>"
        "</Response>"
    )


def _escape_xml(text: str) -> str:
    """Escape special characters for TwiML XML."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


class VoiceHandler:
    """
    Orchestrates the Twilio ↔ Grok AI conversation lifecycle.
    """

    # ------------------------------------------------------------------
    # Incoming call — initial greeting
    # ------------------------------------------------------------------
    @staticmethod
    def handle_incoming_call(request_data: dict, db: Session) -> str:
        """
        Handle a new incoming Twilio call.

        Creates a ``ConversationManager``, determines the clinic from the
        called number, and returns a TwiML greeting with ``<Gather speech>``.
        """
        call_sid = request_data.get("CallSid", "unknown")
        caller = request_data.get("From", "")
        called = request_data.get("To", "")

        logger.info("Incoming call — SID=%s from=%s to=%s", call_sid, caller, called)

        # Look up clinic by Twilio phone number
        clinic = (
            db.query(Clinic)
            .filter(Clinic.twilio_phone_number == called, Clinic.is_active == True)
            .first()
        )

        if not clinic:
            # Fallback: use the first active clinic
            clinic = db.query(Clinic).filter(Clinic.is_active == True).first()

        if not clinic:
            return _twiml_say(
                "Thank you for calling. We are currently unavailable. "
                "Please try again later. Goodbye."
            )

        # Create conversation manager
        grok_client = GrokVoiceClient()
        ConversationManager(
            clinic_id=clinic.id,
            call_sid=call_sid,
            grok_client=grok_client,
        )

        # Build greeting
        clinic_name = clinic.name
        welcome = clinic.welcome_message or f"Thank you for calling {clinic_name}!"

        # Florida two-party consent greeting
        greeting = (
            f"{welcome} "
            f"Just so you know, I'm an AI dental assistant and this call may be "
            f"recorded for quality purposes. How can I help you today?"
        )

        # Check if Spanish greeting should be offered
        if clinic.spanish_enabled:
            greeting += " Para español, diga 'español'."

        return _twiml_say_gather(greeting, language="en")

    # ------------------------------------------------------------------
    # Process speech input
    # ------------------------------------------------------------------
    @staticmethod
    async def process_speech_input(
        speech_text: str,
        call_sid: str,
        db: Session,
    ) -> str:
        """
        Process a Twilio speech recognition result through the
        ConversationManager and return the next TwiML response.
        """
        logger.info("Speech input — SID=%s text='%s'", call_sid, speech_text)

        conversation = ConversationManager.get_conversation(call_sid)
        if not conversation:
            return _twiml_say(
                "I'm sorry, I seem to have lost our conversation. "
                "Please call back and I'll be happy to help. Goodbye!"
            )

        # Process through conversation manager
        response_text, actions = await conversation.process_utterance(speech_text)

        # Check if any action requires a transfer
        for action in actions:
            if action.get("type") == "emergency" and action.get("action") in (
                "transfer_and_911",
                "transfer_to_oncall",
            ):
                # Get on-call number from clinic
                conversation._load_clinic_data()
                on_call_phone = ""
                if conversation._clinic:
                    on_call_phone = conversation._clinic.emergency_contact_phone or ""

                if on_call_phone:
                    return _twiml_transfer(response_text, on_call_phone, conversation.language)
                else:
                    # No on-call number configured — just say the message
                    return _twiml_say_gather(response_text, conversation.language)

        # Check for farewell indicators
        farewell_keywords = [
            "goodbye", "bye", "that's all", "thanks", "thank you",
            "adiós", "gracias", "eso es todo",
        ]
        if any(kw in speech_text.lower() for kw in farewell_keywords):
            farewell = (
                f"{response_text} Thank you for calling! Have a great day!"
                if conversation.language == "en"
                else f"{response_text} ¡Gracias por llamar! ¡Que tenga un buen día!"
            )
            return _twiml_say(farewell, conversation.language)

        # Normal conversational turn — continue gathering
        return _twiml_say_gather(response_text, conversation.language)

    # ------------------------------------------------------------------
    # End call — persist data
    # ------------------------------------------------------------------
    @staticmethod
    def end_call(call_sid: str, db: Session) -> Optional[CallLog]:
        """
        Finalize a call: save the encrypted transcript and create a CallLog.
        Returns the created ``CallLog`` object or ``None``.
        """
        conversation = ConversationManager.end_conversation(call_sid)
        if not conversation:
            logger.warning("end_call for unknown SID=%s", call_sid)
            return None

        transcript = conversation.get_transcript()
        transcript_text = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in transcript
        )

        # Determine sentiment from the conversation
        sentiment = "neutral"
        positive_words = ["thank", "great", "wonderful", "perfect", "appreciate", "gracias"]
        negative_words = ["frustrated", "upset", "angry", "terrible", "horrible", "annoyed"]
        lower_transcript = transcript_text.lower()
        if any(w in lower_transcript for w in positive_words):
            sentiment = "positive"
        elif any(w in lower_transcript for w in negative_words):
            sentiment = "negative"

        # Build actions list
        actions_taken = [a.get("type", "unknown") for a in conversation.actions]

        # Check emergency flag
        is_emergency = any(
            a.get("type") == "emergency" for a in conversation.actions
        )

        # Estimate duration from transcript count
        duration_seconds = len(transcript) * 8  # rough estimate: 8 seconds per turn

        try:
            call_log = CallLog(
                clinic_id=conversation.clinic_id,
                twilio_call_sid=call_sid,
                direction="inbound",
                caller_number="",  # populated from Twilio status callback
                called_number="",
                duration_seconds=duration_seconds,
                status="completed",
                transcript_encrypted=encryption_service.encrypt(transcript_text),
                summary=f"Call with {len(transcript)} exchanges. Actions: {', '.join(actions_taken) or 'none'}",
                sentiment=sentiment,
                language=conversation.language,
                actions_taken=actions_taken,
                is_emergency=is_emergency,
            )
            db.add(call_log)
            db.commit()
            db.refresh(call_log)
            logger.info("CallLog created — id=%s SID=%s", call_log.id, call_sid)
            return call_log
        except Exception as exc:
            db.rollback()
            logger.error("Failed to save CallLog for SID=%s: %s", call_sid, exc)
            return None
