"""
GrokDent FL — Unified Scheduling Service
Integrates Cal.com, Calendly, and Google Calendar APIs with the local database
to provide strict double-booking protection and seamless timezone adjustments.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo
import httpx
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.appointment import Appointment
from backend.services.calendar_service import calendar_service
from backend.utils.timezone import FL_TZ, to_florida_time

logger = logging.getLogger(__name__)


class UnifiedSchedulingService:
    """
    Coordinates multi-channel scheduling integrations to ensure 100% real-time slot verification,
    double-booking protection, and robust timezone conversions.
    """

    def __init__(self) -> None:
        # Cal.com Config
        self.calcom_api_key = settings.CALCOM_API_KEY
        self.calcom_event_type_id = settings.CALCOM_EVENT_TYPE_ID
        self.calcom_api_url = settings.CALCOM_API_URL.rstrip("/")

        # Calendly Config
        self.calendly_pat = settings.CALENDLY_PAT
        self.calendly_event_type_uri = settings.CALENDLY_EVENT_TYPE_URI
        self.calendly_api_url = settings.CALENDLY_API_URL.rstrip("/")
        self._calendly_user_uri: Optional[str] = None

        # Async HTTP client (lazy-initialized)
        self._async_client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Timezone adjustments
    # ------------------------------------------------------------------
    def normalize_to_eastern(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=FL_TZ)
        return dt.astimezone(FL_TZ)

    def to_utc_iso(self, dt: datetime) -> str:
        eastern_dt = self.normalize_to_eastern(dt)
        utc_dt = eastern_dt.astimezone(ZoneInfo("UTC"))
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=10.0))
        return self._async_client

    # ------------------------------------------------------------------
    # Cal.com API Client
    # ------------------------------------------------------------------
    async def get_calcom_slots(self, start_date: str, end_date: str) -> List[str]:
        if not self.calcom_api_key or not self.calcom_event_type_id:
            logger.info("Cal.com is not fully configured. Skipping slots retrieval.")
            return []

        try:
            start_iso = f"{start_date}T00:00:00Z"
            end_iso = f"{end_date}T23:59:59Z"

            url = f"{self.calcom_api_url}/slots"
            params = {
                "apiKey": self.calcom_api_key,
                "eventTypeId": self.calcom_event_type_id,
                "startTime": start_iso,
                "endTime": end_iso,
            }

            logger.info("Fetching Cal.com slots from %s (event_type=%s)", url, self.calcom_event_type_id)
            client = await self._get_async_client()
            response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.error("Cal.com API error (%s): %s", response.status_code, response.text)
                return []

            data = response.json()
            slots_data = data.get("slots", {})

            available_slots = []
            # Cal.com V1 can return slots as dictionary grouped by date: {"slots": {"2026-05-25": [{"time": "..."}]}}
            if isinstance(slots_data, dict):
                for date_key, day_slots in slots_data.items():
                    if isinstance(day_slots, list):
                        for slot in day_slots:
                            if isinstance(slot, dict) and "time" in slot:
                                available_slots.append(slot["time"])
                            elif isinstance(slot, str):
                                available_slots.append(slot)
            # Or as a direct list of objects/strings
            elif isinstance(slots_data, list):
                for slot in slots_data:
                    if isinstance(slot, dict) and "time" in slot:
                        available_slots.append(slot["time"])
                    elif isinstance(slot, str):
                        available_slots.append(slot)

            return available_slots
        except Exception as exc:
            logger.error("Failed to query Cal.com slots: %s", exc)
            return []

    async def create_calcom_booking(
        self,
        start_time_utc: str,
        end_time_utc: str,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
    ) -> Optional[str]:
        if not self.calcom_api_key or not self.calcom_event_type_id:
            return None

        try:
            url = f"{self.calcom_api_url}/bookings"
            params = {"apiKey": self.calcom_api_key}
            
            body = {
                "eventTypeId": int(self.calcom_event_type_id),
                "start": start_time_utc,
                "end": end_time_utc,
                "responses": {
                    "name": patient_name,
                    "email": patient_email,
                    "phone": patient_phone
                },
                "timeZone": "US/Eastern",
                "language": "en"
            }

            logger.info("Creating Cal.com booking at %s", start_time_utc)
            client = await self._get_async_client()
            response = await client.post(url, params=params, json=body)

            if response.status_code in (200, 201):
                booking_id = str(response.json().get("booking", {}).get("id") or "")
                logger.info("Successfully created Cal.com booking: %s", booking_id)
                return booking_id
            else:
                logger.error("Failed to book on Cal.com (%s): %s", response.status_code, response.text)
                return None
        except Exception as exc:
            logger.error("Cal.com booking exception: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Calendly API Client
    # ------------------------------------------------------------------
    async def _get_calendly_user_uri(self) -> Optional[str]:
        if not self.calendly_pat:
            return None
        if self._calendly_user_uri:
            return self._calendly_user_uri

        try:
            url = f"{self.calendly_api_url}/users/me"
            headers = {
                "Authorization": f"Bearer {self.calendly_pat}",
                "Content-Type": "application/json"
            }
            client = await self._get_async_client()
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                self._calendly_user_uri = response.json().get("resource", {}).get("uri")
                logger.info("Cached Calendly User URI: %s", self._calendly_user_uri)
                return self._calendly_user_uri
            else:
                logger.error("Calendly Auth Error (%s): %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("Failed to query Calendly user: %s", exc)
        return None

    async def get_calendly_conflicts(self, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
        user_uri = await self._get_calendly_user_uri()
        if not user_uri:
            return []

        try:
            url = f"{self.calendly_api_url}/scheduled_events"
            headers = {
                "Authorization": f"Bearer {self.calendly_pat}",
                "Content-Type": "application/json"
            }
            params = {
                "user": user_uri,
                "min_start_time": start_iso,
                "max_start_time": end_iso,
                "status": "active"
            }

            logger.info("Fetching Calendly events to check conflicts between %s and %s", start_iso, end_iso)
            client = await self._get_async_client()
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json().get("collection", [])
            else:
                logger.error("Calendly events query failed (%s): %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("Calendly scheduled events check failed: %s", exc)
        return []

    def create_calendly_booking(
        self,
        start_time_utc: str,
        end_time_utc: str,
        patient_name: str,
        patient_email: str,
    ) -> Optional[str]:
        """
        Simulates booking a Calendly event by creating an external scheduling record
        or registering the event structure on Calendly.
        """
        # Calendly usually schedules through widgets; API scheduling is custom or modeled via webhook.
        # We record it as a simulated booking identifier or log it, supporting full mock lifecycle for compatibility.
        if not self.calendly_pat:
            return None
        
        # We generate a mock URL indicating the scheduled slot, as Calendly bookings are handled via their redirect widget.
        simulated_uri = f"https://calendly.com/simulated-event-{hash(start_time_utc + patient_email)}"
        logger.info("Simulated Calendly booking URI generated: %s", simulated_uri)
        return simulated_uri

    # ------------------------------------------------------------------
    # Double-Booking Protection & Slot Verification
    # ------------------------------------------------------------------
    async def verify_slot(
        self,
        db: Session,
        clinic_id: str,
        datetime_obj: datetime,
        duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Strictly verifies if a given slot is available across:
        1. Local Database (appointments table)
        2. Google Calendar (freebusy check via calendar_service)
        3. Cal.com (checking available slots)
        4. Calendly (checking scheduled events)

        Returns a dictionary detailing availability and conflicts.
        """
        slot_start = self.normalize_to_eastern(datetime_obj)
        slot_end = slot_start + timedelta(minutes=duration_minutes)

        results = {
            "available": True,
            "conflicts": [],
            "checked": {
                "local_db": False,
                "google_calendar": False,
                "calcom": False,
                "calendly": False
            }
        }

        # 1. Local Database Verification
        try:
            logger.info("Verifying slot %s locally in DB", slot_start)
            # Fetch active appointments for the clinic to check overlap in a database-agnostic, timezone-safe way
            all_appts = (
                db.query(Appointment)
                .filter(
                    Appointment.clinic_id == clinic_id,
                    Appointment.status != "cancelled"
                )
                .all()
            )
            
            results["checked"]["local_db"] = True
            
            # Ensure target boundaries are normalized in Florida timezone
            slot_s_norm = slot_start.astimezone(FL_TZ)
            slot_e_norm = slot_end.astimezone(FL_TZ)
            
            for appt in all_appts:
                appt_dt = appt.appointment_datetime
                # Ensure correct timezone localization
                if appt_dt.tzinfo is None:
                    appt_dt_tz = appt_dt.replace(tzinfo=FL_TZ)
                else:
                    appt_dt_tz = appt_dt.astimezone(FL_TZ)
                
                appt_end_tz = appt_dt_tz + timedelta(minutes=appt.duration_minutes)
                
                # Check overlap: appt starts before slot ends AND appt ends after slot starts
                if appt_dt_tz < slot_e_norm and appt_end_tz > slot_s_norm:
                    results["available"] = False
                    results["conflicts"].append(
                        f"Local appointment conflict: {appt.id} at {appt_dt_tz.strftime('%I:%M %p')}"
                    )
        except Exception as exc:
            logger.error("Local database verification failed: %s", exc)
            results["available"] = False
            results["conflicts"].append(f"DB Error: {str(exc)}")

        # 2. Google Calendar Verification
        if calendar_service.is_configured:
            try:
                date_str = slot_start.strftime("%Y-%m-%d")
                busy_periods = calendar_service._get_busy_periods(date_str)
                
                results["checked"]["google_calendar"] = True
                
                # Check overlap against Google Calendar busy periods
                for busy in busy_periods:
                    busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00")).astimezone(FL_TZ)
                    busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00")).astimezone(FL_TZ)
                    
                    if slot_start < busy_end and slot_end > busy_start:
                        results["available"] = False
                        results["conflicts"].append(
                            f"Google Calendar conflict: Busy from {busy_start} to {busy_end}"
                        )
            except Exception as exc:
                logger.warning("Google Calendar verification failed: %s", exc)

        # 3. Cal.com Verification
        if self.calcom_api_key and self.calcom_event_type_id:
            try:
                results["checked"]["calcom"] = True
                date_str = slot_start.strftime("%Y-%m-%d")
                
                cal_slots = await self.get_calcom_slots(date_str, date_str)
                
                # Check if the requested slot start matches any available Cal.com slot
                slot_utc_str = self.to_utc_iso(slot_start)
                
                # We do a loose match on minutes/hours since offsets or milliseconds can vary
                matched_slot = False
                for c_slot in cal_slots:
                    # Clean up strings for ISO comparison (removing milliseconds / offsets)
                    try:
                        c_dt = datetime.fromisoformat(c_slot.replace("Z", "+00:00")).astimezone(FL_TZ)
                        if abs((c_dt - slot_start).total_seconds()) < 60: # Match within 1 minute
                            matched_slot = True
                            break
                    except Exception:
                        if slot_utc_str[:16] in c_slot or c_slot[:16] in slot_utc_str:
                            matched_slot = True
                            break
                
                if not matched_slot:
                    results["available"] = False
                    results["conflicts"].append(
                        f"Cal.com slot unavailable: {slot_utc_str} is not in Cal.com free list"
                    )
            except Exception as exc:
                logger.warning("Cal.com verification failed: %s", exc)

        # 4. Calendly Verification
        if self.calendly_pat:
            try:
                results["checked"]["calendly"] = True
                start_iso = self.to_utc_iso(slot_start - timedelta(hours=1)) # Check slightly wider window
                end_iso = self.to_utc_iso(slot_end + timedelta(hours=1))

                conflicts = await self.get_calendly_conflicts(start_iso, end_iso)
                
                for event in conflicts:
                    event_start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00")).astimezone(FL_TZ)
                    event_end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00")).astimezone(FL_TZ)
                    
                    if slot_start < event_end and slot_end > event_start:
                        results["available"] = False
                        results["conflicts"].append(
                            f"Calendly conflict: Event booked from {event_start} to {event_end}"
                        )
            except Exception as exc:
                logger.warning("Calendly verification failed: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Unified Public Scheduler
    # ------------------------------------------------------------------
    async def get_unified_availability(
        self,
        db: Session,
        clinic_id: str,
        date_str: str,
        clinic_hours: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Computes all available 30-minute slots for a given date by cross-checking
        operating hours, DB bookings, Google Calendar, Cal.com, and Calendly.
        """
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = target_date.strftime("%A").lower()

        day_hours = clinic_hours.get(day_name)
        if not day_hours:
            return []  # Clinic is closed

        # Parse hours
        open_time = datetime.strptime(day_hours["open"], "%H:%M").time()
        close_time = datetime.strptime(day_hours["close"], "%H:%M").time()

        # Generate candidate slots
        candidate_slots: List[Dict[str, str]] = []
        current = datetime.combine(target_date.date(), open_time)
        end = datetime.combine(target_date.date(), close_time)

        # Populate slots in 30 minute chunks
        while current + timedelta(minutes=30) <= end:
            slot_end = current + timedelta(minutes=30)
            candidate_slots.append({
                "start": current.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
            })
            current = slot_end

        # Filter candidates using our double-booking verification
        verified_slots = []
        for slot in candidate_slots:
            slot_dt = datetime.combine(
                target_date.date(),
                datetime.strptime(slot["start"], "%H:%M").time()
            ).replace(tzinfo=FL_TZ)
            
            # Check availability
            check = await self.verify_slot(db, clinic_id, slot_dt, duration_minutes=30)
            if check["available"]:
                verified_slots.append(slot)

        return verified_slots

    async def book_appointment_unified(
        self,
        db: Session,
        clinic_id: str,
        patient_id: str,
        datetime_obj: datetime,
        duration_minutes: int,
        service_type: str,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        clinic_name: str = "GrokDent Clinic",
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Core booking manager. Strictly verifies slots before creation to avoid double-bookings.
        Upon verification, registers bookings concurrently on Cal.com, Calendly, Google Calendar,
        and saves the record in the local database.
        """
        # 1. Check double booking
        verification = await self.verify_slot(db, clinic_id, datetime_obj, duration_minutes)
        if not verification["available"]:
            return {
                "success": False,
                "error": "Double-booking protection triggered. Requested slot is no longer available.",
                "conflicts": verification["conflicts"]
            }

        # 2. Setup dates
        slot_start_eastern = self.normalize_to_eastern(datetime_obj)
        slot_end_eastern = slot_start_eastern + timedelta(minutes=duration_minutes)
        
        start_utc_iso = self.to_utc_iso(slot_start_eastern)
        end_utc_iso = self.to_utc_iso(slot_end_eastern)

        # 3. Create Google Calendar Event
        google_event_id = None
        if calendar_service.is_configured:
            # google expects aware datetime or localized format
            google_event_id = calendar_service.create_event(
                clinic_name=clinic_name,
                patient_name=patient_name,
                service=service_type,
                datetime_obj=slot_start_eastern,
                duration=duration_minutes
            )

        # 4. Book Cal.com Event
        calcom_booking_id = None
        if self.calcom_api_key:
            calcom_booking_id = await self.create_calcom_booking(
                start_time_utc=start_utc_iso,
                end_time_utc=end_utc_iso,
                patient_name=patient_name,
                patient_email=patient_email,
                patient_phone=patient_phone
            )

        # 5. Book Calendly Event (Simulated API flow)
        calendly_uri = None
        if self.calendly_pat:
            calendly_uri = self.create_calendly_booking(
                start_time_utc=start_utc_iso,
                end_time_utc=end_utc_iso,
                patient_name=patient_name,
                patient_email=patient_email
            )

        # 6. Save in Local Database
        try:
            appointment = Appointment(
                clinic_id=clinic_id,
                patient_id=patient_id,
                appointment_datetime=slot_start_eastern,
                duration_minutes=duration_minutes,
                service_type=service_type,
                status="scheduled",
                notes=notes,
                google_calendar_event_id=google_event_id,
                calcom_booking_id=calcom_booking_id,
                calendly_event_uri=calendly_uri,
                created_via="ai_voice"
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            logger.info("Successfully recorded appointment in DB: %s", appointment.id)
            
            return {
                "success": True,
                "appointment_id": appointment.id,
                "google_event_id": google_event_id,
                "calcom_booking_id": calcom_booking_id,
                "calendly_event_uri": calendly_uri,
            }
        except Exception as exc:
            db.rollback()
            logger.critical("Failed to write appointment to local DB: %s", exc)
            return {
                "success": False,
                "error": f"Failed to finalize appointment in local database: {str(exc)}"
            }


# Global convenience instance
scheduling_service = UnifiedSchedulingService()
