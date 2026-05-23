"""
GrokDent FL — Google Calendar Service
Syncs appointments with Google Calendar and checks real-time availability.
Falls back to local-only scheduling when Google credentials are not configured.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from backend.config import settings

logger = logging.getLogger(__name__)

# Try importing Google API libraries — they are optional at runtime
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.info("Google API libraries not installed — Calendar sync disabled.")


class GoogleCalendarService:
    """
    Manages calendar events via the Google Calendar API.

    When ``GOOGLE_CALENDAR_CREDENTIALS_JSON`` is empty or ``"{}"``, every
    public method returns a sensible default so the rest of the application
    can operate without Google integration.
    """

    def __init__(self) -> None:
        self._service = None
        self._calendar_id = settings.GOOGLE_CALENDAR_ID or "primary"
        self._initialise_service()

    # ------------------------------------------------------------------
    # Internal setup
    # ------------------------------------------------------------------
    def _initialise_service(self) -> None:
        """Build the Calendar API service object from service-account creds."""
        creds_json = settings.GOOGLE_CALENDAR_CREDENTIALS_JSON
        if not GOOGLE_AVAILABLE or not creds_json or creds_json == "{}":
            logger.info("Google Calendar not configured — running in local-only mode.")
            return

        try:
            creds_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_info,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            self._service = build("calendar", "v3", credentials=credentials)
            logger.info("Google Calendar service initialised for calendar %s", self._calendar_id)
        except Exception as exc:
            logger.error("Failed to initialise Google Calendar: %s", exc)
            self._service = None

    @property
    def is_configured(self) -> bool:
        return self._service is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_availability(
        self,
        date_str: str,
        clinic_hours: Dict,
    ) -> List[Dict[str, str]]:
        """
        Return available 30-minute appointment slots for *date_str* (YYYY-MM-DD)
        based on clinic operating hours and existing Google Calendar events.

        Parameters
        ----------
        date_str : str
            Target date in ``YYYY-MM-DD`` format.
        clinic_hours : dict
            Mapping of day name → ``{"open": "09:00", "close": "17:00"}``.

        Returns
        -------
        list[dict]
            Each dict has ``{"start": "HH:MM", "end": "HH:MM"}``.
        """
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = target_date.strftime("%A").lower()

        day_hours = clinic_hours.get(day_name)
        if not day_hours:
            return []  # clinic closed that day

        open_time = datetime.strptime(day_hours["open"], "%H:%M").time()
        close_time = datetime.strptime(day_hours["close"], "%H:%M").time()

        # Generate all possible 30-min slots
        slots: List[Dict[str, str]] = []
        current = datetime.combine(target_date.date(), open_time)
        end = datetime.combine(target_date.date(), close_time)

        while current + timedelta(minutes=30) <= end:
            slot_end = current + timedelta(minutes=30)
            slots.append({
                "start": current.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
            })
            current = slot_end

        # If Google is configured, remove busy slots
        if self.is_configured:
            try:
                busy_slots = self._get_busy_periods(date_str)
                slots = [
                    s for s in slots
                    if not self._slot_conflicts(s, busy_slots, target_date)
                ]
            except Exception as exc:
                logger.warning("Could not fetch Google busy times: %s — returning all slots", exc)

        return slots

    def create_event(
        self,
        clinic_name: str,
        patient_name: str,
        service: str,
        datetime_obj: datetime,
        duration: int = 30,
    ) -> Optional[str]:
        """
        Create a Google Calendar event and return the event ID.
        Returns ``None`` if Google is not configured.
        """
        if not self.is_configured:
            logger.info("Google Calendar not configured — skipping event creation.")
            return None

        event_body = {
            "summary": f"{service} — {patient_name}",
            "description": (
                f"Clinic: {clinic_name}\n"
                f"Patient: {patient_name}\n"
                f"Service: {service}\n"
                f"Booked via GrokDent FL AI Receptionist"
            ),
            "start": {
                "dateTime": datetime_obj.isoformat(),
                "timeZone": "US/Eastern",
            },
            "end": {
                "dateTime": (datetime_obj + timedelta(minutes=duration)).isoformat(),
                "timeZone": "US/Eastern",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 1440},  # 24 hours
                ],
            },
        }

        try:
            event = (
                self._service.events()
                .insert(calendarId=self._calendar_id, body=event_body)
                .execute()
            )
            event_id = event.get("id")
            logger.info("Created Google Calendar event %s", event_id)
            return event_id
        except Exception as exc:
            logger.error("Failed to create Google Calendar event: %s", exc)
            return None

    def delete_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event.  Returns ``True`` on success."""
        if not self.is_configured or not event_id:
            return False

        try:
            self._service.events().delete(
                calendarId=self._calendar_id, eventId=event_id
            ).execute()
            logger.info("Deleted Google Calendar event %s", event_id)
            return True
        except Exception as exc:
            logger.error("Failed to delete Google Calendar event %s: %s", event_id, exc)
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_busy_periods(self, date_str: str) -> list:
        """Query Google Calendar freebusy API for the given date."""
        start = f"{date_str}T00:00:00-05:00"
        end = f"{date_str}T23:59:59-05:00"

        body = {
            "timeMin": start,
            "timeMax": end,
            "timeZone": "US/Eastern",
            "items": [{"id": self._calendar_id}],
        }

        result = self._service.freebusy().query(body=body).execute()
        return result["calendars"][self._calendar_id].get("busy", [])

    @staticmethod
    def _slot_conflicts(
        slot: Dict[str, str],
        busy_periods: list,
        target_date: datetime,
    ) -> bool:
        """Check whether a candidate slot overlaps any busy period."""
        slot_start = datetime.combine(
            target_date.date(),
            datetime.strptime(slot["start"], "%H:%M").time(),
        )
        slot_end = datetime.combine(
            target_date.date(),
            datetime.strptime(slot["end"], "%H:%M").time(),
        )

        for busy in busy_periods:
            busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
            # Overlap condition
            if slot_start < busy_end and slot_end > busy_start:
                return True
        return False


# Module-level convenience instance
calendar_service = GoogleCalendarService()
