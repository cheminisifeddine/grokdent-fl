"""
GrokDent FL — Emergency Detection Service
Scans patient utterances for dental emergency keywords, classifies severity,
and generates clinically appropriate response instructions.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Emergency keyword definitions with severity tiers
# ---------------------------------------------------------------------------
EMERGENCY_KEYWORDS: List[Dict] = [
    # --- CRITICAL (immediate transfer) ---
    {"phrase": "can't breathe", "severity": "critical", "category": "airway"},
    {"phrase": "cannot breathe", "severity": "critical", "category": "airway"},
    {"phrase": "trouble breathing", "severity": "critical", "category": "airway"},
    {"phrase": "allergic reaction", "severity": "critical", "category": "allergy"},
    {"phrase": "anaphylaxis", "severity": "critical", "category": "allergy"},
    {"phrase": "throat swelling", "severity": "critical", "category": "allergy"},
    {"phrase": "broken jaw", "severity": "critical", "category": "trauma"},
    {"phrase": "jaw broken", "severity": "critical", "category": "trauma"},
    {"phrase": "bleeding heavily", "severity": "critical", "category": "hemorrhage"},
    {"phrase": "won't stop bleeding", "severity": "critical", "category": "hemorrhage"},
    {"phrase": "uncontrollable bleeding", "severity": "critical", "category": "hemorrhage"},
    {"phrase": "passed out", "severity": "critical", "category": "syncope"},
    {"phrase": "unconscious", "severity": "critical", "category": "syncope"},

    # --- HIGH (same-day, urgent) ---
    {"phrase": "knocked out tooth", "severity": "high", "category": "avulsion"},
    {"phrase": "tooth knocked out", "severity": "high", "category": "avulsion"},
    {"phrase": "tooth fell out", "severity": "high", "category": "avulsion"},
    {"phrase": "avulsed tooth", "severity": "high", "category": "avulsion"},
    {"phrase": "severe pain", "severity": "high", "category": "pain"},
    {"phrase": "extreme pain", "severity": "high", "category": "pain"},
    {"phrase": "unbearable pain", "severity": "high", "category": "pain"},
    {"phrase": "worst pain", "severity": "high", "category": "pain"},
    {"phrase": "abscess", "severity": "high", "category": "infection"},
    {"phrase": "pus coming", "severity": "high", "category": "infection"},
    {"phrase": "facial swelling", "severity": "high", "category": "infection"},
    {"phrase": "face is swollen", "severity": "high", "category": "infection"},
    {"phrase": "swelling", "severity": "high", "category": "infection"},
    {"phrase": "fever and tooth", "severity": "high", "category": "infection"},
    {"phrase": "broken tooth", "severity": "high", "category": "fracture"},
    {"phrase": "cracked tooth", "severity": "high", "category": "fracture"},
    {"phrase": "tooth broke", "severity": "high", "category": "fracture"},
    {"phrase": "chipped tooth", "severity": "high", "category": "fracture"},

    # --- MODERATE (schedule soon) ---
    {"phrase": "lost filling", "severity": "moderate", "category": "restoration"},
    {"phrase": "filling fell out", "severity": "moderate", "category": "restoration"},
    {"phrase": "crown fell off", "severity": "moderate", "category": "restoration"},
    {"phrase": "lost crown", "severity": "moderate", "category": "restoration"},
    {"phrase": "loose tooth", "severity": "moderate", "category": "mobility"},
    {"phrase": "tooth is moving", "severity": "moderate", "category": "mobility"},
    {"phrase": "gum bleeding", "severity": "moderate", "category": "periodontal"},
    {"phrase": "gums are bleeding", "severity": "moderate", "category": "periodontal"},
    {"phrase": "tooth pain", "severity": "moderate", "category": "pain"},
    {"phrase": "toothache", "severity": "moderate", "category": "pain"},
    {"phrase": "sensitive to hot", "severity": "moderate", "category": "sensitivity"},
    {"phrase": "sensitive to cold", "severity": "moderate", "category": "sensitivity"},
]

# Pre-compile regex patterns for efficient matching
_PATTERNS = [
    {
        "pattern": re.compile(re.escape(kw["phrase"]), re.IGNORECASE),
        "severity": kw["severity"],
        "category": kw["category"],
        "phrase": kw["phrase"],
    }
    for kw in EMERGENCY_KEYWORDS
]

# Severity ranking for choosing the highest severity match
_SEVERITY_ORDER = {"critical": 3, "high": 2, "moderate": 1}

# ---------------------------------------------------------------------------
# Emergency response templates
# ---------------------------------------------------------------------------
EMERGENCY_RESPONSES: Dict[str, Dict] = {
    "critical": {
        "instructions_en": (
            "This sounds like a medical emergency. Please call 911 immediately. "
            "I am transferring you to our on-call dentist right now."
        ),
        "instructions_es": (
            "Esto parece una emergencia médica. Por favor llame al 911 inmediatamente. "
            "Le estoy transfiriendo a nuestro dentista de guardia ahora mismo."
        ),
        "action": "transfer_and_911",
        "triage_priority": 1,
    },
    "high": {
        "instructions_en": (
            "I understand you're in a lot of pain. This is a dental emergency and "
            "we want to see you as soon as possible. Let me transfer you to our "
            "on-call dentist who can help you right away."
        ),
        "instructions_es": (
            "Entiendo que tiene mucho dolor. Esto es una emergencia dental y "
            "queremos atenderle lo antes posible. Permítame transferirle a nuestro "
            "dentista de guardia que puede ayudarle ahora mismo."
        ),
        "action": "transfer_to_oncall",
        "triage_priority": 2,
        "home_care": {
            "avulsion": (
                "If your tooth was knocked out: pick it up by the crown (not the root), "
                "rinse gently with milk or saline, and try to place it back in the socket. "
                "If you can't, put it in a cup of milk. Time is critical — we need to "
                "see you within 30 minutes for the best chance of saving it."
            ),
            "infection": (
                "Rinse your mouth with warm salt water (1/2 teaspoon salt in 8 oz water). "
                "Do not apply heat to the outside of your face. Take ibuprofen for pain "
                "if you can. Do NOT pop or drain any swelling yourself."
            ),
            "pain": (
                "Take ibuprofen (Advil) 400-600mg for pain relief. "
                "Apply a cold compress to the outside of your cheek for 20 minutes on, "
                "20 minutes off. Avoid very hot or cold foods."
            ),
            "fracture": (
                "Rinse your mouth with warm water. If there's bleeding, apply gauze with "
                "gentle pressure. Save any broken tooth pieces. Apply a cold compress to "
                "reduce swelling. Avoid chewing on that side."
            ),
        },
    },
    "moderate": {
        "instructions_en": (
            "I'm sorry you're experiencing that. Let me schedule an appointment "
            "for you as soon as possible so our dentist can take a look."
        ),
        "instructions_es": (
            "Lamento que esté experimentando eso. Permítame programar una cita "
            "lo antes posible para que nuestro dentista pueda evaluarle."
        ),
        "action": "schedule_urgent",
        "triage_priority": 3,
    },
}


class EmergencyService:
    """
    Detects dental emergencies in patient utterances and generates
    clinically appropriate response instructions.
    """

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    @staticmethod
    def detect_emergency(text: str) -> Tuple[bool, str, List[str]]:
        """
        Scan *text* for emergency keywords.

        Returns
        -------
        tuple
            ``(is_emergency, severity, matched_keywords)``
            where *severity* is one of ``"critical"``, ``"high"``,
            ``"moderate"``, or ``""`` if no match.
        """
        if not text:
            return False, "", []

        matched: List[Dict] = []
        for entry in _PATTERNS:
            if entry["pattern"].search(text):
                matched.append(entry)

        if not matched:
            return False, "", []

        # Return the highest severity found
        matched.sort(key=lambda m: _SEVERITY_ORDER.get(m["severity"], 0), reverse=True)
        highest_severity = matched[0]["severity"]
        matched_phrases = list({m["phrase"] for m in matched})

        logger.warning(
            "Emergency detected — severity=%s keywords=%s",
            highest_severity, matched_phrases,
        )
        return True, highest_severity, matched_phrases

    # ------------------------------------------------------------------
    # Response generation
    # ------------------------------------------------------------------
    @staticmethod
    def get_emergency_response(
        severity: str,
        clinic: Optional[object] = None,
        language: str = "en",
    ) -> Dict:
        """
        Generate an emergency response with instructions and transfer info.

        Parameters
        ----------
        severity : str
            ``"critical"``, ``"high"``, or ``"moderate"``.
        clinic : Clinic, optional
            SQLAlchemy Clinic object for on-call contact information.
        language : str
            ``"en"`` or ``"es"``.

        Returns
        -------
        dict
            Response object with instructions, action, and contact details.
        """
        response_template = EMERGENCY_RESPONSES.get(severity, EMERGENCY_RESPONSES["moderate"])

        instructions_key = "instructions_es" if language == "es" else "instructions_en"

        response = {
            "severity": severity,
            "instructions": response_template[instructions_key],
            "action": response_template["action"],
            "triage_priority": response_template["triage_priority"],
            "emergency_numbers": {
                "911": "911",
                "poison_control": "1-800-222-1222",
            },
        }

        # Add home care tips for high-severity emergencies
        if severity == "high" and "home_care" in response_template:
            response["home_care_tips"] = response_template["home_care"]

        # Add clinic on-call info if available
        if clinic:
            response["on_call"] = {
                "name": getattr(clinic, "emergency_contact_name", None) or "On-call dentist",
                "phone": getattr(clinic, "emergency_contact_phone", None) or "See clinic phone",
                "clinic_phone": getattr(clinic, "phone", None) or "",
            }
        else:
            response["on_call"] = {
                "name": "On-call dentist",
                "phone": "Contact the clinic directly",
            }

        return response


# Module-level convenience instance
emergency_service = EmergencyService()
