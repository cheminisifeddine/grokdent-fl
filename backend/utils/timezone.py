"""
GrokDent FL — Timezone Utilities
All date/time helpers use US/Eastern for Florida.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

# Florida uses Eastern Time
FL_TZ = ZoneInfo("US/Eastern")


def get_florida_now() -> datetime:
    """Return the current datetime in US/Eastern (Florida)."""
    return datetime.now(FL_TZ)


def to_florida_time(utc_dt: datetime) -> datetime:
    """Convert a UTC-aware datetime to US/Eastern."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(FL_TZ)


def _format_time(dt: datetime) -> str:
    """Cross-platform hour:min AM/PM formatting."""
    hour = dt.hour
    minute = dt.minute
    ampm = "AM" if hour < 12 else "PM"
    hour12 = hour % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12}:{minute:02d} {ampm}"


def format_appointment_time(dt: datetime) -> str:
    if dt.tzinfo is None or str(dt.tzinfo) != "US/Eastern":
        dt = to_florida_time(dt)
    day = dt.day
    month = dt.strftime("%B")
    weekday = dt.strftime("%A")
    time_str = _format_time(dt)
    return f"{weekday}, {month} {day} at {time_str}"


def format_time_short(dt: datetime) -> str:
    if dt.tzinfo is None or str(dt.tzinfo) != "US/Eastern":
        dt = to_florida_time(dt)
    return _format_time(dt)


def get_business_hours_status(hours_dict: Optional[Dict]) -> Tuple[bool, str]:
    """
    Determine whether the clinic is currently open based on its hours config.

    Parameters
    ----------
    hours_dict : dict | None
        Mapping like ``{"monday": {"open": "08:00", "close": "17:00"}, ...}``

    Returns
    -------
    tuple[bool, str]
        ``(is_open, message)`` — e.g. ``(True, "We're currently open until 5:00 PM")``.
    """
    if not hours_dict:
        return False, "Our office hours are not available at this time."

    now = get_florida_now()
    day_name = now.strftime("%A").lower()

    day_hours = hours_dict.get(day_name)
    if not day_hours:
        # Clinic is closed today — find next open day
        next_open = _find_next_open_day(hours_dict, now)
        return False, f"We're closed today. {next_open}"

    try:
        open_time = datetime.strptime(day_hours["open"], "%H:%M").time()
        close_time = datetime.strptime(day_hours["close"], "%H:%M").time()
    except (KeyError, ValueError):
        return False, "Our office hours are not available at this time."

    current_time = now.time()

    if current_time < open_time:
        open_str = _format_time_from_str(day_hours["open"])
        return False, f"We're not open yet today. We open at {open_str}."
    elif current_time >= close_time:
        next_open = _find_next_open_day(hours_dict, now)
        return False, f"We've closed for today. {next_open}"
    else:
        close_str = _format_time_from_str(day_hours["close"])
        return True, f"We're currently open until {close_str}."


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _format_time_from_str(time_str: str) -> str:
    """Convert ``'17:00'`` to ``'5:00 PM'``."""
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%-I:%M %p").replace(" 0", " ")
    except ValueError:
        return time_str


def _find_next_open_day(hours_dict: Dict, now: datetime) -> str:
    """Return a human-readable string about when the clinic next opens."""
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    current_idx = day_names.index(now.strftime("%A").lower())

    for offset in range(1, 8):
        next_idx = (current_idx + offset) % 7
        next_day = day_names[next_idx]
        if next_day in hours_dict:
            open_str = _format_time_from_str(hours_dict[next_day]["open"])
            friendly_day = next_day.capitalize()
            return f"We reopen {friendly_day} at {open_str}."

    return "Please call us for our current hours."
