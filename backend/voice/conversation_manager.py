"""
GrokDent FL — Conversation Manager
Maintains per-call conversation state and orchestrates the AI receptionist
flow through greeting → identification → intent → action → farewell.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from backend.voice.grok_client import GrokVoiceClient
from backend.voice.dental_prompts import (
    build_system_prompt,
    build_spanish_prompt,
    BOOKING_PROMPT,
    INSURANCE_PROMPT,
    EMERGENCY_PROMPT,
)
from backend.voice.language_router import LanguageRouter
from backend.services.emergency_service import emergency_service
from backend.database import SessionLocal
from backend.models.clinic import Clinic
from backend.models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Finite-state machine states for a receptionist conversation."""
    GREETING = "greeting"
    IDENTIFY = "identify"
    INTENT = "intent"
    BOOKING = "booking"
    FAQ = "faq"
    INSURANCE = "insurance"
    EMERGENCY = "emergency"
    FAREWELL = "farewell"


# Intent keywords
BOOKING_KEYWORDS = [
    "appointment", "schedule", "book", "reserve", "cita", "programar", "agendar",
    "reschedule", "cancel", "change", "cambiar", "cancelar", "reprogramar",
]
INSURANCE_KEYWORDS = [
    "insurance", "coverage", "accept", "copay", "deductible",
    "seguro", "cobertura", "aceptan",
]
FAQ_KEYWORDS = [
    "hours", "location", "address", "cost", "price", "service",
    "horario", "ubicación", "dirección", "costo", "precio", "servicio",
    "parking", "dentist", "doctor", "sedation", "whitening", "implant",
]


class ConversationManager:
    """
    Manages a single phone-call conversation with a patient.

    Each active call is tracked in the class-level ``conversations`` dict
    keyed by Twilio Call SID.
    """

    # Class-level store of active conversations
    conversations: Dict[str, "ConversationManager"] = {}

    def __init__(
        self,
        clinic_id: str,
        call_sid: str,
        grok_client: Optional[GrokVoiceClient] = None,
    ) -> None:
        self.clinic_id = clinic_id
        self.call_sid = call_sid
        self.grok_client = grok_client or GrokVoiceClient()

        self.state = ConversationState.GREETING
        self.language = "en"
        self.history: List[Dict[str, Any]] = []
        self.patient_info: Dict[str, str] = {}
        self.actions: List[Dict[str, Any]] = []
        self.system_prompt: str = ""
        self._clinic = None
        self._kb_entries: List = []

        # Register this conversation
        ConversationManager.conversations[call_sid] = self
        logger.info("Conversation started — SID=%s clinic=%s", call_sid, clinic_id)

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def _load_clinic_data(self) -> None:
        """Load clinic and KB from the database (called once per conversation)."""
        if self._clinic is not None:
            return

        db = SessionLocal()
        try:
            self._clinic = db.query(Clinic).filter(Clinic.id == self.clinic_id).first()
            if self._clinic:
                self._kb_entries = (
                    db.query(KnowledgeBase)
                    .filter(
                        KnowledgeBase.clinic_id == self.clinic_id,
                        KnowledgeBase.is_active == True,
                    )
                    .order_by(KnowledgeBase.priority.desc())
                    .all()
                )
                # Convert ORM objects to dicts while session is open
                self._kb_entries = [
                    {
                        "question": kb.question,
                        "answer": kb.answer,
                        "answer_spanish": kb.answer_spanish,
                        "category": kb.category,
                    }
                    for kb in self._kb_entries
                ]
        finally:
            db.close()

    def _ensure_system_prompt(self) -> None:
        """Build the system prompt if not yet built."""
        if self.system_prompt:
            return
        self._load_clinic_data()
        if not self._clinic:
            self.system_prompt = (
                "You are a dental office AI receptionist. "
                "Be helpful, professional, and empathetic."
            )
            return

        if self.language == "es":
            self.system_prompt = build_spanish_prompt(self._clinic, self._kb_entries)
        else:
            self.system_prompt = build_system_prompt(self._clinic, self._kb_entries)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def process_utterance(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Process a patient utterance and return ``(response_text, actions)``.

        The ``actions`` list may contain dicts like:
        ``{"type": "book_appointment", "data": {...}}``
        ``{"type": "transfer", "target": "on_call"}``
        """
        self._ensure_system_prompt()

        # Detect language from the input
        detected_lang = LanguageRouter.detect_language(text)
        if detected_lang != self.language:
            self.language = detected_lang
            # Rebuild prompt in the new language
            self.system_prompt = ""
            self._ensure_system_prompt()

        # Record the user utterance
        self.history.append({
            "role": "user",
            "content": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # --- Emergency check (overrides all other flows) ---
        is_emergency, severity, keywords = emergency_service.detect_emergency(text)
        if is_emergency and severity in ("critical", "high"):
            response = await self.handle_emergency(text)
            return response, self.actions

        # --- State-based routing ---
        if self.state == ConversationState.GREETING:
            # After greeting, detect intent
            intent = await self.detect_intent(text)
            self.state = self._intent_to_state(intent)

        if self.state == ConversationState.BOOKING:
            response = await self.handle_booking(text)
        elif self.state == ConversationState.INSURANCE:
            response = await self.handle_insurance(text)
        elif self.state == ConversationState.EMERGENCY:
            response = await self.handle_emergency(text)
        elif self.state == ConversationState.FAQ:
            response = await self.handle_faq(text)
        else:
            # General intent detection for subsequent utterances
            intent = await self.detect_intent(text)
            new_state = self._intent_to_state(intent)
            if new_state != ConversationState.INTENT:
                self.state = new_state
                return await self.process_utterance(text)
            response = await self.handle_faq(text)

        # Record the assistant response
        self.history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return response, list(self.actions)

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------
    async def detect_intent(self, text: str) -> str:
        """Classify the patient's intent from their utterance."""
        text_lower = text.lower()

        # Keyword-based fast path
        if any(kw in text_lower for kw in BOOKING_KEYWORDS):
            return "booking"
        if any(kw in text_lower for kw in INSURANCE_KEYWORDS):
            return "insurance"

        # Emergency keywords
        is_emergency, severity, _ = emergency_service.detect_emergency(text)
        if is_emergency:
            return "emergency"

        if any(kw in text_lower for kw in FAQ_KEYWORDS):
            return "faq"

        return "general"

    # ------------------------------------------------------------------
    # Patient info extraction
    # ------------------------------------------------------------------
    async def extract_patient_info(self, text: str) -> Dict[str, str]:
        """Extract patient information from the utterance using Grok."""
        extraction_prompt = (
            "Extract any patient information from the following text. "
            "Return ONLY a JSON object with keys: first_name, last_name, phone, "
            "dob, insurance_provider, insurance_id, service_needed, preferred_date, preferred_time. "
            "Use null for any field not mentioned. Text: " + text
        )

        try:
            result = await self.grok_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": extraction_prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )

            import json
            extracted = json.loads(result)
            # Merge into patient_info (only non-null values)
            for key, value in extracted.items():
                if value and value != "null":
                    self.patient_info[key] = value
        except Exception as exc:
            logger.warning("Patient info extraction failed: %s", exc)

        return self.patient_info

    # ------------------------------------------------------------------
    # Flow handlers
    # ------------------------------------------------------------------
    async def handle_booking(self, text: str) -> str:
        """Handle appointment booking conversation."""
        # Extract patient info from this utterance
        await self.extract_patient_info(text)

        # Build conversation messages for Grok
        messages = [{"role": m["role"], "content": m["content"]} for m in self.history[:-1]]

        response = await self.grok_client.dental_response(
            system_prompt=self.system_prompt,
            conversation_history=messages,
            patient_input=text,
        )

        # If we have enough info, flag a booking action
        if (
            self.patient_info.get("first_name")
            and self.patient_info.get("service_needed")
            and (self.patient_info.get("preferred_date") or self.patient_info.get("preferred_time"))
        ):
            self.actions.append({
                "type": "book_appointment",
                "data": dict(self.patient_info),
            })

        return response

    async def handle_faq(self, text: str) -> str:
        """Handle FAQ / general question flow."""
        messages = [{"role": m["role"], "content": m["content"]} for m in self.history[:-1]]
        return await self.grok_client.dental_response(
            system_prompt=self.system_prompt,
            conversation_history=messages,
            patient_input=text,
        )

    async def handle_insurance(self, text: str) -> str:
        """Handle insurance inquiry flow."""
        self.state = ConversationState.INSURANCE
        messages = [{"role": m["role"], "content": m["content"]} for m in self.history[:-1]]
        return await self.grok_client.dental_response(
            system_prompt=self.system_prompt,
            conversation_history=messages,
            patient_input=text,
        )

    async def handle_emergency(self, text: str) -> str:
        """Handle emergency triage flow."""
        self.state = ConversationState.EMERGENCY
        self._load_clinic_data()

        is_emergency, severity, keywords = emergency_service.detect_emergency(text)
        emergency_response = emergency_service.get_emergency_response(
            severity=severity or "moderate",
            clinic=self._clinic,
            language=self.language,
        )

        # Record emergency action
        self.actions.append({
            "type": "emergency",
            "severity": severity,
            "keywords": keywords,
            "action": emergency_response.get("action"),
        })

        # If critical or high, provide the pre-built response immediately
        if severity in ("critical", "high"):
            return emergency_response["instructions"]

        # For moderate, use Grok for a more natural response
        messages = [{"role": m["role"], "content": m["content"]} for m in self.history[:-1]]
        return await self.grok_client.dental_response(
            system_prompt=self.system_prompt,
            conversation_history=messages,
            patient_input=text,
        )

    # ------------------------------------------------------------------
    # Transcript
    # ------------------------------------------------------------------
    def get_transcript(self) -> List[Dict[str, Any]]:
        """Return the full conversation transcript."""
        return list(self.history)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _intent_to_state(intent: str) -> ConversationState:
        """Map an intent string to a conversation state."""
        mapping = {
            "booking": ConversationState.BOOKING,
            "insurance": ConversationState.INSURANCE,
            "emergency": ConversationState.EMERGENCY,
            "faq": ConversationState.FAQ,
        }
        return mapping.get(intent, ConversationState.INTENT)

    @classmethod
    def get_conversation(cls, call_sid: str) -> Optional["ConversationManager"]:
        """Retrieve an active conversation by call SID."""
        return cls.conversations.get(call_sid)

    @classmethod
    def end_conversation(cls, call_sid: str) -> Optional["ConversationManager"]:
        """Remove and return a conversation from the active store."""
        return cls.conversations.pop(call_sid, None)
