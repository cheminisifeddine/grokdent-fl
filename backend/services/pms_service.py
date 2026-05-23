"""
GrokDent FL — Practice Management System (PMS) Service
Mock implementation simulating a dental PMS integration.
Returns realistic data modelled on Florida dental practice workflows
including ADA procedure codes, patient records, and treatment history.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ADA procedure code database (subset most common in general dentistry)
# ---------------------------------------------------------------------------
ADA_CODES: Dict[str, List[Dict]] = {
    "cleaning": [
        {"code": "D1110", "description": "Prophylaxis — Adult", "fee": 125.00},
        {"code": "D1120", "description": "Prophylaxis — Child", "fee": 85.00},
    ],
    "deep cleaning": [
        {"code": "D4341", "description": "Periodontal Scaling & Root Planing (per quadrant)", "fee": 275.00},
        {"code": "D4342", "description": "Periodontal Scaling — 1-3 teeth per quadrant", "fee": 200.00},
    ],
    "exam": [
        {"code": "D0120", "description": "Periodic Oral Evaluation", "fee": 65.00},
        {"code": "D0150", "description": "Comprehensive Oral Evaluation — New Patient", "fee": 95.00},
    ],
    "x-ray": [
        {"code": "D0210", "description": "Full Mouth Radiographs (FMX)", "fee": 150.00},
        {"code": "D0220", "description": "Periapical — First Radiographic Image", "fee": 35.00},
        {"code": "D0274", "description": "Bitewings — Four Radiographic Images", "fee": 65.00},
    ],
    "filling": [
        {"code": "D2140", "description": "Amalgam — One Surface, Primary", "fee": 175.00},
        {"code": "D2150", "description": "Amalgam — Two Surfaces, Primary", "fee": 220.00},
        {"code": "D2330", "description": "Resin Composite — One Surface, Anterior", "fee": 195.00},
        {"code": "D2331", "description": "Resin Composite — Two Surfaces, Anterior", "fee": 250.00},
    ],
    "crown": [
        {"code": "D2740", "description": "Crown — Porcelain/Ceramic", "fee": 1200.00},
        {"code": "D2750", "description": "Crown — Porcelain Fused to High Noble Metal", "fee": 1150.00},
    ],
    "root canal": [
        {"code": "D3310", "description": "Endodontic Therapy — Anterior Tooth", "fee": 850.00},
        {"code": "D3320", "description": "Endodontic Therapy — Premolar", "fee": 950.00},
        {"code": "D3330", "description": "Endodontic Therapy — Molar", "fee": 1200.00},
    ],
    "extraction": [
        {"code": "D7140", "description": "Extraction — Erupted Tooth/Exposed Root", "fee": 225.00},
        {"code": "D7210", "description": "Surgical Extraction", "fee": 350.00},
    ],
    "whitening": [
        {"code": "D9972", "description": "External Bleaching — Per Arch", "fee": 350.00},
        {"code": "D9975", "description": "External Bleaching — Per Tooth (Custom Tray)", "fee": 125.00},
    ],
    "implant": [
        {"code": "D6010", "description": "Endosteal Implant", "fee": 2500.00},
        {"code": "D6065", "description": "Implant-Supported Porcelain Crown", "fee": 1800.00},
    ],
    "dentures": [
        {"code": "D5110", "description": "Complete Denture — Maxillary", "fee": 1800.00},
        {"code": "D5120", "description": "Complete Denture — Mandibular", "fee": 1800.00},
        {"code": "D5213", "description": "Partial Denture — Maxillary, Cast Framework", "fee": 1600.00},
    ],
    "veneer": [
        {"code": "D2962", "description": "Labial Veneer — Porcelain Laminate", "fee": 1100.00},
    ],
    "emergency": [
        {"code": "D9110", "description": "Palliative Treatment of Dental Pain", "fee": 150.00},
        {"code": "D0140", "description": "Limited Oral Evaluation — Problem Focused", "fee": 85.00},
    ],
    "orthodontics": [
        {"code": "D8080", "description": "Comprehensive Orthodontic Treatment — Adolescent", "fee": 5500.00},
        {"code": "D8090", "description": "Comprehensive Orthodontic Treatment — Adult", "fee": 6000.00},
    ],
    "sealant": [
        {"code": "D1351", "description": "Sealant — Per Tooth", "fee": 55.00},
    ],
    "fluoride": [
        {"code": "D1206", "description": "Topical Fluoride Varnish", "fee": 40.00},
    ],
    "night guard": [
        {"code": "D9944", "description": "Occlusal Guard — Hard Appliance", "fee": 450.00},
    ],
}


class MockPMSService:
    """
    Simulated dental Practice Management System integration.

    In production this would call the clinic's actual PMS API (Dentrix,
    Eaglesoft, Open Dental, etc.).  For development and demo purposes
    it returns realistic mock data representative of Florida dental offices.
    """

    # ------------------------------------------------------------------
    # Patient search
    # ------------------------------------------------------------------
    @staticmethod
    def search_patient(
        name: Optional[str] = None,
        dob: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for a patient by name and/or date of birth.
        Returns a list of matching patient records.
        """
        logger.info("PMS patient search — name=%s dob=%s", name, dob)

        # Mock patient database (FL-realistic names)
        mock_patients = [
            {
                "id": "PMS-1001",
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "dob": "1985-03-15",
                "phone": "(305) 555-0123",
                "email": "maria.rodriguez@email.com",
                "insurance": "Delta Dental PPO",
                "member_id": "DDL-789456123",
                "last_visit": "2026-02-10",
                "next_due": "2026-08-10",
                "balance": 0.00,
            },
            {
                "id": "PMS-1002",
                "first_name": "James",
                "last_name": "Thompson",
                "dob": "1972-07-22",
                "phone": "(407) 555-0456",
                "email": "jthompson@email.com",
                "insurance": "Cigna DPPO",
                "member_id": "CIG-321654987",
                "last_visit": "2026-01-05",
                "next_due": "2026-07-05",
                "balance": 125.00,
            },
            {
                "id": "PMS-1003",
                "first_name": "Sofia",
                "last_name": "Garcia",
                "dob": "1990-11-08",
                "phone": "(813) 555-0789",
                "email": "sofia.g@email.com",
                "insurance": "Humana DHMO",
                "member_id": "HUM-456789012",
                "last_visit": "2025-12-20",
                "next_due": "2026-06-20",
                "balance": 45.00,
            },
            {
                "id": "PMS-1004",
                "first_name": "Robert",
                "last_name": "Williams",
                "dob": "1968-05-30",
                "phone": "(954) 555-0234",
                "email": "rwilliams68@email.com",
                "insurance": "MetLife PDP",
                "member_id": "MET-654321789",
                "last_visit": "2026-03-01",
                "next_due": "2026-09-01",
                "balance": 0.00,
            },
            {
                "id": "PMS-1005",
                "first_name": "Isabella",
                "last_name": "Martinez",
                "dob": "1995-09-14",
                "phone": "(321) 555-0567",
                "email": "isabella.m@email.com",
                "insurance": "Guardian Dental",
                "member_id": "GDN-987654321",
                "last_visit": "2026-04-15",
                "next_due": "2026-10-15",
                "balance": 200.00,
            },
        ]

        results = mock_patients  # start with all
        if name:
            name_lower = name.lower()
            results = [
                p for p in results
                if name_lower in p["first_name"].lower()
                or name_lower in p["last_name"].lower()
                or name_lower in f"{p['first_name']} {p['last_name']}".lower()
            ]
        if dob:
            results = [p for p in results if p["dob"] == dob]

        return results

    # ------------------------------------------------------------------
    # Appointment creation
    # ------------------------------------------------------------------
    @staticmethod
    def create_appointment(data: Dict) -> Dict:
        """
        Create an appointment in the PMS.
        Returns the created appointment record.
        """
        logger.info("PMS appointment creation — %s", data)

        appointment = {
            "id": f"PMS-APT-{uuid.uuid4().hex[:8].upper()}",
            "patient_id": data.get("patient_id", "PMS-1001"),
            "patient_name": data.get("patient_name", "Unknown Patient"),
            "provider": data.get("provider", "Dr. Patel"),
            "service": data.get("service", "General Exam"),
            "datetime": data.get("datetime", datetime.now(timezone.utc).isoformat()),
            "duration_minutes": data.get("duration_minutes", 30),
            "status": "scheduled",
            "operatory": data.get("operatory", "Op 3"),
            "notes": data.get("notes", ""),
            "insurance_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return appointment

    # ------------------------------------------------------------------
    # Treatment / procedure codes
    # ------------------------------------------------------------------
    @staticmethod
    def get_treatment_codes(service: str) -> List[Dict]:
        """
        Look up ADA procedure codes for a given service type.
        The *service* string is matched case-insensitively against our code DB.
        """
        service_lower = service.lower().strip()

        # Direct match
        if service_lower in ADA_CODES:
            return ADA_CODES[service_lower]

        # Fuzzy match — check if the service keyword appears in any key
        for key, codes in ADA_CODES.items():
            if service_lower in key or key in service_lower:
                return codes

        logger.warning("No ADA codes found for service '%s'", service)
        return [
            {
                "code": "D0999",
                "description": f"Unspecified procedure — {service}",
                "fee": 0.00,
            }
        ]

    # ------------------------------------------------------------------
    # Provider schedule (mock)
    # ------------------------------------------------------------------
    @staticmethod
    def get_provider_schedule(provider: str = "Dr. Patel", date_str: str = "") -> Dict:
        """Return the provider's schedule for a given date."""
        return {
            "provider": provider,
            "date": date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "working_hours": {"start": "08:00", "end": "17:00"},
            "lunch": {"start": "12:00", "end": "13:00"},
            "booked_slots": [
                {"time": "09:00", "duration": 60, "patient": "Existing Patient"},
                {"time": "14:00", "duration": 30, "patient": "Existing Patient"},
            ],
            "available_slots": [
                "08:00", "08:30", "10:00", "10:30", "11:00", "11:30",
                "13:00", "13:30", "14:30", "15:00", "15:30", "16:00", "16:30",
            ],
        }


# Module-level convenience instance
pms_service = MockPMSService()
