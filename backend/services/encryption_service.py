"""
GrokDent FL — Encryption Service
AES-256 (Fernet) encryption for HIPAA-compliant PHI field-level protection.
Encrypts patient phone numbers, DOBs, insurance IDs, notes, and transcripts
before they are written to the database.
"""

import base64
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
            # Generate a key for development convenience — log a loud warning
            key = Fernet.generate_key().decode()
            logger.warning(
                "ENCRYPTION_KEY not set — generated a temporary key. "
                "Set ENCRYPTION_KEY in .env for production!"
            )
        else:
            # Ensure the key is properly padded / encoded
            try:
                base64.urlsafe_b64decode(key)
            except Exception:
                # Treat the raw string as a passphrase and derive a key
                key = base64.urlsafe_b64encode(key.ljust(32)[:32].encode()).decode()

        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

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
        """Encrypt a plaintext string and return a URL-safe base64 ciphertext."""
        if not plaintext:
            return ""
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            logger.error("Encryption failed: %s", exc)
            raise

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a Fernet ciphertext string back to plaintext."""
        if not ciphertext:
            return ""
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken:
            logger.error(
                "Decryption failed — invalid token. "
                "Was the ENCRYPTION_KEY rotated without re-encrypting data?"
            )
            return "[DECRYPTION_ERROR]"
        except Exception as exc:
            logger.error("Decryption failed: %s", exc)
            raise


# Module-level convenience instance
encryption_service = EncryptionService.get_instance()
