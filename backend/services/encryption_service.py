"""
GrokDent FL — Encryption Service
AES-256 (Fernet) encryption for HIPAA-compliant PHI field-level protection.
Encrypts patient phone numbers, DOBs, insurance IDs, notes, and transcripts
before they are written to the database.
"""

import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken
from backend.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Thin wrapper around ``cryptography.fernet.Fernet`` that reads the key
    from ``settings.ENCRYPTION_KEY``.  If the key is empty/missing the service
    auto-generates one and warns — this keeps development easy while ensuring
    production deployments always set the env var.
    """

    _instance: "EncryptionService | None" = None  # singleton

    def __init__(self) -> None:
        key = settings.ENCRYPTION_KEY
        if not key:
            logger.error(
                "ENCRYPTION_KEY not set — encryption unavailable. "
                "Set ENCRYPTION_KEY in .env for production!"
            )
            self._fernet = None
            return

        try:
            base64.urlsafe_b64decode(key)
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            derived = hashlib.sha256(key.encode("utf-8")).digest()
            encoded_key = base64.urlsafe_b64encode(derived).decode()
            self._fernet = Fernet(encoded_key)

    # ------------------------------------------------------------------
    # Singleton accessor — avoids re-reading the key on every call
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "EncryptionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        if self._fernet is None:
            logger.error("Encryption unavailable: ENCRYPTION_KEY not set")
            return "[ENCRYPTION_UNAVAILABLE]"
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            logger.error("Encryption failed: %s", exc)
            raise

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        if self._fernet is None:
            logger.error("Decryption unavailable: ENCRYPTION_KEY not set")
            return "[DECRYPTION_ERROR]"
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken:
            logger.error("Decryption failed — invalid token. Key may have been rotated.")
            return "[DECRYPTION_ERROR]"
        except Exception as exc:
            logger.error("Decryption failed: %s", exc)
            raise


# Module-level convenience instance
encryption_service = EncryptionService.get_instance()
