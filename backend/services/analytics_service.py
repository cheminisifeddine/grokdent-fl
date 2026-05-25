"""
GrokDent FL — Analytics Service
Provides dashboard KPIs, time-series data, and aggregate statistics
for a clinic's calls, appointments, and patient activity.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, Date
from sqlalchemy.orm import Session

from backend.models.call_log import CallLog
from backend.models.appointment import Appointment

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    All methods are static so they can be called without instantiation.
    Each method takes a ``clinic_id`` and an active ``db`` session.
    """

    # ------------------------------------------------------------------
    # Dashboard KPIs
    # ------------------------------------------------------------------
    @staticmethod
    def get_dashboard_metrics(clinic_id: str, db: Session) -> Dict:
        """
        Return headline metrics for the clinic dashboard.

        Returns dict with:
            calls_today, calls_week, calls_month,
            bookings_today, bookings_week,
            revenue_estimate, avg_call_duration, satisfaction_score
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())  # Monday
        month_start = today_start.replace(day=1)

        # --- Call counts ---
        calls_today = (
            db.query(func.count(CallLog.id))
            .filter(CallLog.clinic_id == clinic_id, CallLog.created_at >= today_start)
            .scalar() or 0
        )
        calls_week = (
            db.query(func.count(CallLog.id))
            .filter(CallLog.clinic_id == clinic_id, CallLog.created_at >= week_start)
            .scalar() or 0
        )
        calls_month = (
            db.query(func.count(CallLog.id))
            .filter(CallLog.clinic_id == clinic_id, CallLog.created_at >= month_start)
            .scalar() or 0
        )

        # --- Booking counts ---
        bookings_today = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.clinic_id == clinic_id,
                Appointment.created_at >= today_start,
                Appointment.status != "cancelled",
            )
            .scalar() or 0
        )
        bookings_week = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.clinic_id == clinic_id,
                Appointment.created_at >= week_start,
                Appointment.status != "cancelled",
            )
            .scalar() or 0
        )

        # --- Revenue estimate (sum of booked appointments this month × avg $150) ---
        bookings_month = (
            db.query(func.count(Appointment.id))
            .filter(
                Appointment.clinic_id == clinic_id,
                Appointment.created_at >= month_start,
                Appointment.status.in_(["scheduled", "confirmed", "completed"]),
            )
            .scalar() or 0
        )
        revenue_estimate = round(bookings_month * 150.0, 2)

        # --- Average call duration ---
        avg_duration = (
            db.query(func.avg(CallLog.duration_seconds))
            .filter(CallLog.clinic_id == clinic_id, CallLog.duration_seconds > 0)
            .scalar()
        )
        avg_call_duration = round(float(avg_duration), 1) if avg_duration else 0.0

        # --- Satisfaction score (% positive sentiment) ---
        total_scored = (
            db.query(func.count(CallLog.id))
            .filter(
                CallLog.clinic_id == clinic_id,
                CallLog.sentiment.in_(["positive", "neutral", "negative"]),
            )
            .scalar() or 0
        )
        positive = (
            db.query(func.count(CallLog.id))
            .filter(CallLog.clinic_id == clinic_id, CallLog.sentiment == "positive")
            .scalar() or 0
        )
        satisfaction_score = round((positive / total_scored * 100), 1) if total_scored else 100.0

        return {
            "calls_today": calls_today,
            "calls_week": calls_week,
            "calls_month": calls_month,
            "bookings_today": bookings_today,
            "bookings_week": bookings_week,
            "revenue_estimate": revenue_estimate,
            "avg_call_duration": avg_call_duration,
            "satisfaction_score": satisfaction_score,
        }

    # ------------------------------------------------------------------
    # Time-series: calls over time
    # ------------------------------------------------------------------
    @staticmethod
    def get_calls_over_time(clinic_id: str, days: int, db: Session) -> List[Dict]:
        """Return daily call counts for the past *days* days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        rows = (
            db.query(
                func.date(CallLog.created_at).label("date"),
                func.count(CallLog.id).label("count"),
            )
            .filter(CallLog.clinic_id == clinic_id, CallLog.created_at >= since)
            .group_by(func.date(CallLog.created_at))
            .order_by(func.date(CallLog.created_at))
            .all()
        )

        # Fill in missing days with zero
        result = []
        current = since.date()
        today = datetime.now(timezone.utc).date()
        row_map = {r.date if isinstance(r.date, str) else str(r.date): r.count for r in rows}

        while current <= today:
            date_str = str(current)
            result.append({"date": date_str, "count": row_map.get(date_str, 0)})
            current += timedelta(days=1)

        return result

    # ------------------------------------------------------------------
    # Time-series: bookings over time
    # ------------------------------------------------------------------
    @staticmethod
    def get_bookings_over_time(clinic_id: str, days: int, db: Session) -> List[Dict]:
        """Return daily booking counts for the past *days* days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        rows = (
            db.query(
                func.date(Appointment.created_at).label("date"),
                func.count(Appointment.id).label("count"),
            )
            .filter(
                Appointment.clinic_id == clinic_id,
                Appointment.created_at >= since,
                Appointment.status != "cancelled",
            )
            .group_by(func.date(Appointment.created_at))
            .order_by(func.date(Appointment.created_at))
            .all()
        )

        result = []
        current = since.date()
        today = datetime.now(timezone.utc).date()
        row_map = {r.date if isinstance(r.date, str) else str(r.date): r.count for r in rows}

        while current <= today:
            date_str = str(current)
            result.append({"date": date_str, "count": row_map.get(date_str, 0)})
            current += timedelta(days=1)

        return result

    # ------------------------------------------------------------------
    # Top services
    # ------------------------------------------------------------------
    @staticmethod
    def get_top_services(clinic_id: str, db: Session) -> List[Dict]:
        """Return ranked list of most-booked services."""
        rows = (
            db.query(
                Appointment.service_type,
                func.count(Appointment.id).label("count"),
            )
            .filter(
                Appointment.clinic_id == clinic_id,
                Appointment.service_type.isnot(None),
                Appointment.status != "cancelled",
            )
            .group_by(Appointment.service_type)
            .order_by(func.count(Appointment.id).desc())
            .limit(10)
            .all()
        )
        return [{"service": row.service_type, "count": row.count} for row in rows]

    # ------------------------------------------------------------------
    # Language breakdown
    # ------------------------------------------------------------------
    @staticmethod
    def get_language_stats(clinic_id: str, db: Session) -> Dict[str, int]:
        """Return call counts broken down by language (en / es)."""
        rows = (
            db.query(
                CallLog.language,
                func.count(CallLog.id).label("count"),
            )
            .filter(CallLog.clinic_id == clinic_id)
            .group_by(CallLog.language)
            .all()
        )
        stats: Dict[str, int] = {"en": 0, "es": 0}
        for row in rows:
            lang = row.language or "en"
            stats[lang] = stats.get(lang, 0) + row.count
        return stats
