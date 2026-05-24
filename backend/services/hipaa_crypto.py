"""
GrokDent FL — HIPAA-Compliant Encryption Service
Implements AES-256-GCM (Authenticated Encryption with Associated Data - AEAD)
for strict at-rest PHI protection.
"""

import base64
import os
import hashlib
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.config import settings

logger = logging.getLogger(__name__)


class HIPAACryptoService:
    """
    Implements AES-256-GCM for patient intake profiles and highly sensitive PHI.
    
    - Key derivation: PBKDF2 or SHA-256 hash to ensure a strict 256-bit key.
    - IV / Nonce: 12-byte cryptographically secure random values.
    - AEAD: Ensures confidentiality, integrity, and authenticity.
    - Associated Data (AD): Protects against swap/context-substitution attacks.
    """

    def __init__(self) -> None:
        key_source = settings.ENCRYPTION_KEY
        if not key_source:
            logger.error(
                "ENCRYPTION_KEY not set — HIPAA encryption unavailable. "
                "Set ENCRYPTION_KEY in .env for production!"
            )
            self._aesgcm = None
            return
        self._key = hashlib.sha256(key_source.encode("utf-8")).digest()
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str, associated_data: str = None) -> str:
        if not plaintext:
            return ""
        if self._aesgcm is None:
            logger.error("HIPAA encryption unavailable: ENCRYPTION_KEY not set")
            return "[ENCRYPTION_UNAVAILABLE]"
        try:
            nonce = os.urandom(12)
            data_bytes = plaintext.encode("utf-8")
            ad_bytes = associated_data.encode("utf-8") if associated_data else None
            ciphertext_with_tag = self._aesgcm.encrypt(nonce, data_bytes, ad_bytes)
            combined = nonce + ciphertext_with_tag
            return base64.urlsafe_b64encode(combined).decode("utf-8")
        except Exception as exc:
            logger.error("HIPAA AES-256-GCM Encryption failed: %s", exc)
            raise

    def decrypt(self, ciphertext: str, associated_data: str = None) -> str:
        if not ciphertext:
            return ""
        if self._aesgcm is None:
            logger.error("HIPAA decryption unavailable: ENCRYPTION_KEY not set")
            return "[DECRYPTION_ERROR]"
        try:
            combined = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
            if len(combined) < 28:
                raise ValueError("Ciphertext payload too short for valid AES-256-GCM")
            nonce = combined[:12]
            actual_ciphertext = combined[12:]
            ad_bytes = associated_data.encode("utf-8") if associated_data else None
            decrypted_bytes = self._aesgcm.decrypt(nonce, actual_ciphertext, ad_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            logger.error("HIPAA AES-256-GCM Decryption failed: %s", exc)
            return "[DECRYPTION_ERROR]"


# Global convenience instance
hipaa_crypto = HIPAACryptoService()
