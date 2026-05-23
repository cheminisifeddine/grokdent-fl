"""
GrokDent FL — Insurance Verification Service
Simulates real-time eligibility verification for Florida dental insurance
providers.  In production this would integrate with payer APIs or a
clearinghouse like Availity, DentalXChange, or Tesia.
"""

import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Florida dental insurance provider database
# ---------------------------------------------------------------------------
FL_INSURANCE_DB: Dict[str, Dict] = {
    "delta dental": {
        "name": "Delta Dental of Florida",
        "type": "PPO",
        "phone": "(800) 521-2651",
        "website": "https://www.deltadentalins.com",
        "annual_max": 2000.00,
        "deductible": 50.00,
        "preventive_coverage": 100,  # percent
        "basic_coverage": 80,
        "major_coverage": 50,
        "waiting_period_basic": 0,
        "waiting_period_major": 12,  # months
        "orthodontic_coverage": 50,
        "ortho_lifetime_max": 1500.00,
    },
    "humana": {
        "name": "Humana Dental (Florida DHMO)",
        "type": "DHMO",
        "phone": "(800) 233-4013",
        "website": "https://www.humana.com/dental-insurance",
        "annual_max": 0,  # DHMO = copay based, no annual max
        "deductible": 0.00,
        "preventive_coverage": 100,
        "basic_coverage": 70,
        "major_coverage": 50,
        "waiting_period_basic": 0,
        "waiting_period_major": 6,
        "orthodontic_coverage": 0,
        "ortho_lifetime_max": 0,
        "copay_schedule": True,
    },
    "mcna dental": {
        "name": "MCNA Dental (Florida Medicaid)",
        "type": "Medicaid",
        "phone": "(855) 776-6262",
        "website": "https://www.mcnafl.net",
        "annual_max": 0,  # Medicaid — no annual max concept
        "deductible": 0.00,
        "preventive_coverage": 100,
        "basic_coverage": 100,
        "major_coverage": 100,
        "waiting_period_basic": 0,
        "waiting_period_major": 0,
        "orthodontic_coverage": 100,
        "ortho_lifetime_max": 0,
        "notes": "Florida Healthy Kids / SMILES program",
    },
    "guardian": {
        "name": "Guardian Dental",
        "type": "PPO",
        "phone": "(888) 482-7342",
        "website": "https://www.guardiandirect.com",
        "annual_max": 1500.00,
        "deductible": 75.00,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "waiting_period_basic": 6,
        "waiting_period_major": 12,
        "orthodontic_coverage": 50,
        "ortho_lifetime_max": 1000.00,
    },
    "cigna": {
        "name": "Cigna Dental PPO",
        "type": "PPO",
        "phone": "(800) 244-6224",
        "website": "https://www.cigna.com/dental",
        "annual_max": 1500.00,
        "deductible": 50.00,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "waiting_period_basic": 0,
        "waiting_period_major": 12,
        "orthodontic_coverage": 50,
        "ortho_lifetime_max": 1500.00,
    },
    "metlife": {
        "name": "MetLife Preferred Dentist Program (PDP)",
        "type": "PPO",
        "phone": "(800) 275-4638",
        "website": "https://www.metlife.com/dental",
        "annual_max": 2000.00,
        "deductible": 50.00,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "waiting_period_basic": 0,
        "waiting_period_major": 12,
        "orthodontic_coverage": 50,
        "ortho_lifetime_max": 1500.00,
    },
    "aetna": {
        "name": "Aetna Dental",
        "type": "PPO",
        "phone": "(877) 238-6200",
        "website": "https://www.aetna.com/individuals-families/dental-insurance.html",
        "annual_max": 1750.00,
        "deductible": 50.00,
        "preventive_coverage": 100,
        "basic_coverage": 80,
        "major_coverage": 50,
        "waiting_period_basic": 0,
        "waiting_period_major": 12,
        "orthodontic_coverage": 50,
        "ortho_lifetime_max": 1500.00,
    },
}

# ADA code → coverage tier mapping
PROCEDURE_TIERS: Dict[str, str] = {
    "D0120": "preventive", "D0150": "preventive",
    "D0210": "preventive", "D0220": "preventive", "D0274": "preventive",
    "D1110": "preventive", "D1120": "preventive",
    "D1206": "preventive", "D1351": "preventive",
    "D2140": "basic", "D2150": "basic",
    "D2330": "basic", "D2331": "basic",
    "D7140": "basic", "D7210": "basic",
    "D4341": "basic", "D4342": "basic",
    "D2740": "major", "D2750": "major",
    "D3310": "major", "D3320": "major", "D3330": "major",
    "D5110": "major", "D5120": "major", "D5213": "major",
    "D6010": "major", "D6065": "major",
    "D2962": "major",
    "D9944": "basic",
    "D9972": "cosmetic", "D9975": "cosmetic",
    "D8080": "orthodontic", "D8090": "orthodontic",
}


class InsuranceService:
    """
    Dental insurance verification and coverage lookup.
    Returns realistic mock data modelled on actual Florida dental plan
    structures and benefit levels.
    """

    # ------------------------------------------------------------------
    # Eligibility verification
    # ------------------------------------------------------------------
    @staticmethod
    def verify_eligibility(
        provider: str,
        member_id: str,
        patient_name: str,
    ) -> Dict:
        """
        Verify a patient's dental insurance eligibility.

        Parameters
        ----------
        provider : str
            Insurance company name (fuzzy-matched).
        member_id : str
            Member / subscriber ID.
        patient_name : str
            Patient's full name.

        Returns
        -------
        dict
            Eligibility result with coverage percentages, annual maximums,
            deductible, remaining benefits, and status.
        """
        logger.info(
            "Insurance eligibility check — provider=%s member=%s patient=%s",
            provider, member_id, patient_name,
        )

        # Fuzzy-match provider
        plan = InsuranceService._match_provider(provider)
        if not plan:
            return {
                "eligible": False,
                "provider": provider,
                "member_id": member_id,
                "error": f"Provider '{provider}' not found in our database.",
                "message": (
                    "We could not verify your insurance automatically. "
                    "Please bring your insurance card to your appointment "
                    "and we will verify manually."
                ),
            }

        # Simulate a realistic eligibility response
        used_amount = round(random.uniform(0, plan["annual_max"] * 0.6), 2) if plan["annual_max"] else 0
        remaining = round(plan["annual_max"] - used_amount, 2) if plan["annual_max"] else None

        return {
            "eligible": True,
            "provider": plan["name"],
            "type": plan["type"],
            "member_id": member_id,
            "patient_name": patient_name,
            "coverage": {
                "preventive": plan["preventive_coverage"],
                "basic": plan["basic_coverage"],
                "major": plan["major_coverage"],
            },
            "annual_max": plan["annual_max"] if plan["annual_max"] else "N/A (copay-based)",
            "deductible": plan["deductible"],
            "deductible_met": round(plan["deductible"] * random.uniform(0, 1), 2),
            "remaining_benefits": remaining,
            "used_this_year": used_amount,
            "orthodontic_coverage": plan["orthodontic_coverage"],
            "ortho_lifetime_max": plan["ortho_lifetime_max"],
            "waiting_periods": {
                "basic_months": plan["waiting_period_basic"],
                "major_months": plan["waiting_period_major"],
            },
            "phone": plan["phone"],
            "website": plan["website"],
            "verified_at": "2026-05-23T17:00:00-04:00",
            "message": (
                f"Coverage verified for {patient_name} under {plan['name']}. "
                f"{'Remaining annual benefits: $' + str(remaining) if remaining else 'Copay-based plan.'}"
            ),
        }

    # ------------------------------------------------------------------
    # Provider listing
    # ------------------------------------------------------------------
    @staticmethod
    def get_florida_providers() -> List[Dict]:
        """Return all Florida dental insurance providers with plan details."""
        return [
            {
                "name": plan["name"],
                "type": plan["type"],
                "phone": plan["phone"],
                "website": plan["website"],
                "annual_max": plan["annual_max"],
                "deductible": plan["deductible"],
                "preventive_coverage": f"{plan['preventive_coverage']}%",
                "basic_coverage": f"{plan['basic_coverage']}%",
                "major_coverage": f"{plan['major_coverage']}%",
            }
            for plan in FL_INSURANCE_DB.values()
        ]

    # ------------------------------------------------------------------
    # Procedure coverage lookup
    # ------------------------------------------------------------------
    @staticmethod
    def check_coverage(
        provider: str,
        procedure_code: str,
    ) -> Dict:
        """
        Check how a specific procedure is covered by an insurance provider.

        Returns the coverage tier, percentage, and estimated patient cost.
        """
        plan = InsuranceService._match_provider(provider)
        if not plan:
            return {
                "covered": False,
                "provider": provider,
                "procedure_code": procedure_code,
                "error": "Provider not found",
            }

        tier = PROCEDURE_TIERS.get(procedure_code, "major")

        if tier == "cosmetic":
            return {
                "covered": False,
                "provider": plan["name"],
                "procedure_code": procedure_code,
                "tier": "cosmetic",
                "coverage_pct": 0,
                "message": "Cosmetic procedures are typically not covered by dental insurance.",
            }

        if tier == "orthodontic":
            coverage_pct = plan.get("orthodontic_coverage", 0)
        else:
            coverage_key = f"{tier}_coverage"
            coverage_pct = plan.get(coverage_key, 0)

        return {
            "covered": coverage_pct > 0,
            "provider": plan["name"],
            "procedure_code": procedure_code,
            "tier": tier,
            "coverage_pct": coverage_pct,
            "patient_responsibility_pct": 100 - coverage_pct,
            "deductible_applies": tier in ("basic", "major"),
            "waiting_period_months": plan.get(f"waiting_period_{tier}", 0) if tier in ("basic", "major") else 0,
            "message": (
                f"{plan['name']} covers this {tier} procedure at {coverage_pct}%. "
                f"Patient is responsible for {100 - coverage_pct}% of the fee."
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _match_provider(provider: str) -> Optional[Dict]:
        """Fuzzy-match a provider name against our database."""
        provider_lower = provider.lower().strip()
        # Direct key match
        if provider_lower in FL_INSURANCE_DB:
            return FL_INSURANCE_DB[provider_lower]
        # Partial match
        for key, plan in FL_INSURANCE_DB.items():
            if key in provider_lower or provider_lower in key:
                return plan
            if provider_lower in plan["name"].lower():
                return plan
        return None


# Module-level convenience instance
insurance_service = InsuranceService()
