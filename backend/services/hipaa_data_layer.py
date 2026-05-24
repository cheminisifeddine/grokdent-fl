"""
GrokDent FL — HIPAA Data Isolation Layer
Provides a unified interface for encrypting/decrypting all PHI fields
across models, ensuring consistent key management and audit tracking.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.services.encryption_service import encryption_service
from backend.services.hipaa_crypto import hipaa_crypto

logger = logging.getLogger(__name__)


class HIPAADataLayer:
    """
    Singleton that centralizes PHI encryption/decryption.

    Uses Fernet (AES-128-CBC + HMAC) for most fields and
    AES-256-GCM for high-sensitivity intake profiles.
    """

    _instance: Optional["HIPAADataLayer"] = None

    PHI_FIELDS = {
        "patient": ["phone", "email", "dob", "insurance_id", "notes"],
        "call_log": ["transcript"],
        "intake": [
            "first_name", "last_name", "phone", "email",
            "dob", "ssn_last_four", "insurance_id",
            "medical_history", "medications", "notes",
        ],
    }

    def __init__(self):
        self._encryption_service = encryption_service
        self._hipaa_crypto = hipaa_crypto

    @classmethod
    def get_instance(cls) -> "HIPAADataLayer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def encrypt_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        for field in self.PHI_FIELDS["patient"]:
            if field in result and result[field]:
                encrypted = self._encryption_service.encrypt(str(result[field]))
                result[f"{field}_encrypted"] = encrypted
                del result[field]
        return result

    def decrypt_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        for field in self.PHI_FIELDS["patient"]:
            enc_key = f"{field}_encrypted"
            if enc_key in result and result[enc_key]:
                plain = self._encryption_service.decrypt(str(result[enc_key]))
                if plain and plain != "[DECRYPTION_ERROR]":
                    result[field] = plain
        return result

    def encrypt_call_transcript(self, transcript: str) -> str:
        return self._encryption_service.encrypt(transcript)

    def decrypt_call_transcript(self, encrypted: str) -> str:
        return self._encryption_service.decrypt(encrypted)

    def encrypt_intake_profile(self, data: Dict[str, Any], clinic_id: str) -> Dict[str, Any]:
        result = dict(data)
        for field in self.PHI_FIELDS["intake"]:
            if field in result and result[field]:
                encrypted = self._hipaa_crypto.encrypt(
                    str(result[field]),
                    associated_data=clinic_id,
                )
                result[f"{field}_encrypted"] = encrypted
                del result[field]
        result["hipaa_encrypted_at"] = datetime.now(timezone.utc).isoformat()
        return result

    def decrypt_intake_profile(self, data: Dict[str, Any], clinic_id: str) -> Dict[str, Any]:
        result = dict(data)
        for field in self.PHI_FIELDS["intake"]:
            enc_key = f"{field}_encrypted"
            if enc_key in result and result[enc_key]:
                plain = self._hipaa_crypto.decrypt(
                    str(result[enc_key]),
                    associated_data=clinic_id,
                )
                if plain and plain != "[DECRYPTION_ERROR]":
                    result[field] = plain
        return result

    def audit_event(self, action: str, resource_type: str, resource_id: str, clinic_id: str, user_id: Optional[str] = None):
        logger.info(
            "HIPAA Audit — action=%s resource=%s id=%s clinic=%s user=%s",
            action, resource_type, resource_id, clinic_id, user_id or "system",
        )


hipaa_data_layer = HIPAADataLayer.get_instance()
