"""
GrokDent FL — Language Router
Detects whether a patient is speaking English or Spanish and provides
language-appropriate greetings and on-the-fly translation via Grok.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Spanish language indicators (common words/phrases)
# ---------------------------------------------------------------------------
SPANISH_INDICATORS = [
    "hola", "buenos días", "buenas tardes", "buenas noches",
    "necesito", "quiero", "tengo", "puedo", "puede",
    "cita", "dolor", "diente", "muela", "dentista",
    "por favor", "gracias", "ayuda", "emergencia",
    "seguro", "limpieza", "empaste", "corona",
    "español", "hablar", "sí", "no puedo",
    "me duele", "cuánto cuesta", "cuándo",
    "aceptan", "horario", "dónde", "dirección",
]

# Pre-compile a single pattern for fast matching
_SPANISH_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in SPANISH_INDICATORS) + r")\b",
    re.IGNORECASE,
)


class LanguageRouter:
    """
    Lightweight language detection and routing for bilingual support.

    Uses keyword matching rather than a heavy ML model because:
    1. Phone-call utterances are short (< 30 words)
    2. The two target languages (EN/ES) are highly distinguishable
    3. Latency matters on a live call
    """

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect whether *text* is English or Spanish.

        Returns ``'en'`` or ``'es'``.  Defaults to ``'en'`` when ambiguous.
        """
        if not text:
            return "en"

        matches = _SPANISH_PATTERN.findall(text.lower())

        # If 2+ Spanish keywords found, or if the word "español" appears, → Spanish
        if len(matches) >= 2:
            return "es"
        if "español" in text.lower() or "espanol" in text.lower():
            return "es"

        # Count word-level heuristic: common Spanish function words
        spanish_function_words = {"el", "la", "los", "las", "un", "una", "de", "en", "que", "es", "y", "por", "para", "con", "al", "del"}
        words = set(text.lower().split())
        spanish_count = len(words & spanish_function_words)

        if spanish_count >= 3:
            return "es"

        return "en"

    # ------------------------------------------------------------------
    # Greetings
    # ------------------------------------------------------------------
    @staticmethod
    def get_greeting(language: str, clinic_name: str) -> str:
        """Return a language-appropriate greeting for the clinic."""
        if language == "es":
            return (
                f"¡Gracias por llamar a {clinic_name}! "
                f"Soy su asistente dental con inteligencia artificial. "
                f"Esta llamada puede ser grabada para fines de calidad. "
                f"¿En qué puedo ayudarle hoy?"
            )
        return (
            f"Thank you for calling {clinic_name}! "
            f"I'm your AI dental assistant. "
            f"This call may be recorded for quality purposes. "
            f"How can I help you today?"
        )

    # ------------------------------------------------------------------
    # Translation via Grok
    # ------------------------------------------------------------------
    @staticmethod
    async def translate_if_needed(
        text: str,
        target_lang: str,
        grok_client,
    ) -> str:
        """
        Translate *text* to *target_lang* using Grok if it's not already
        in the target language.  Returns the original text if Grok is
        unavailable or the text is already in the target language.
        """
        current_lang = LanguageRouter.detect_language(text)
        if current_lang == target_lang:
            return text

        lang_names = {"en": "English", "es": "Spanish"}
        target_name = lang_names.get(target_lang, "English")

        try:
            result = await grok_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional medical translator. "
                            f"Translate the following text to {target_name}. "
                            f"Maintain the original meaning, tone, and any "
                            f"dental/medical terminology. Return ONLY the translation."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return result.strip()
        except Exception as exc:
            logger.warning("Translation failed: %s — returning original", exc)
            return text
