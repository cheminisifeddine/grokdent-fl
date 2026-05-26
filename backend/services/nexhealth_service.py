"""
GrokDent FL — NexHealth PMS Integration Service
Live integration connecting the AI Receptionist to US dental Practice Management Systems
(Dentrix, Eaglesoft, OpenDental) via the NexHealth universal API.
"""

import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from backend.config import settings

logger = logging.getLogger(__name__)

class NexHealthService:
    """
    Production US Clinical integration with NexHealth.
    Requires NEXHEALTH_API_KEY to be set in the environment.
    """
    
    def __init__(self):
        self.api_key = settings.NEXHEALTH_API_KEY
        self.base_url = settings.NEXHEALTH_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def search_patient(self, name: Optional[str] = None, dob: Optional[str] = None) -> List[Dict]:
        """Search for a patient via NexHealth API. Falls back to mock if not configured."""
        if not self._is_configured():
            from backend.services.pms_service import MockPMSService
            return MockPMSService.search_patient(name, dob)
            
        logger.info("NexHealth: Searching for patient name=%s, dob=%s", name, dob)
        async with httpx.AsyncClient() as client:
            try:
                # Real implementation would query /patients endpoint
                response = await client.get(
                    f"{self.base_url}/patients",
                    params={"name": name, "dob": dob},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                # Map NexHealth patient schema to our expected schema
                data = response.json().get("data", [])
                return [self._map_patient(p) for p in data]
            except Exception as e:
                logger.error("NexHealth patient search failed: %s", e)
                return []

    async def create_appointment(self, data: Dict) -> Dict:
        """Create an appointment via NexHealth API."""
        if not self._is_configured():
            from backend.services.pms_service import MockPMSService
            return MockPMSService.create_appointment(data)
            
        logger.info("NexHealth: Creating appointment %s", data)
        async with httpx.AsyncClient() as client:
            try:
                # NexHealth appointment creation
                payload = {
                    "patient_id": data.get("patient_id"),
                    "provider_id": data.get("provider"),
                    "start_time": data.get("datetime"),
                    "duration": data.get("duration_minutes", 30),
                    "appointment_type": data.get("service")
                }
                response = await client.post(
                    f"{self.base_url}/appointments",
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("data", {})
            except Exception as e:
                logger.error("NexHealth appointment creation failed: %s", e)
                raise

    def get_treatment_codes(self, service: str) -> List[Dict]:
        """Get treatment codes. Typically ADA codes are static or fetched from PMS."""
        # For ADA codes, we can reuse the mock's static database since ADA codes are standard
        from backend.services.pms_service import MockPMSService
        return MockPMSService.get_treatment_codes(service)

    async def get_provider_schedule(self, provider: str = "Dr. Patel", date_str: str = "") -> Dict:
        """Fetch provider availability from NexHealth."""
        if not self._is_configured():
            from backend.services.pms_service import MockPMSService
            return MockPMSService.get_provider_schedule(provider, date_str)
            
        logger.info("NexHealth: Fetching schedule for provider %s on %s", provider, date_str)
        async with httpx.AsyncClient() as client:
            try:
                # Query provider availability
                response = await client.get(
                    f"{self.base_url}/availability",
                    params={"provider_id": provider, "date": date_str},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("data", {})
            except Exception as e:
                logger.error("NexHealth availability check failed: %s", e)
                # Fallback on failure
                return {"available_slots": []}

    def _map_patient(self, nexhealth_patient: Dict) -> Dict:
        """Map NexHealth patient schema to our expected format."""
        return {
            "id": str(nexhealth_patient.get("id")),
            "first_name": nexhealth_patient.get("first_name", ""),
            "last_name": nexhealth_patient.get("last_name", ""),
            "dob": nexhealth_patient.get("date_of_birth", ""),
            "phone": nexhealth_patient.get("mobile_phone", ""),
            "email": nexhealth_patient.get("email", ""),
        }

# Singleton instance
nexhealth_pms = NexHealthService()
