"""
Tests for backend/services/analytics_service.py — dashboard KPIs, time-series, top services.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from backend.services.analytics_service import AnalyticsService
from tests.conftest import create_test_call, create_test_appointment


class TestAnalyticsDashboardMetrics:
    """Dashboard headline KPI calculations."""

    def test_empty_clinic_returns_zeros(self, db: Session, sample_clinic):
        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        assert metrics["calls_today"] == 0
        assert metrics["calls_week"] == 0
        assert metrics["calls_month"] == 0
        assert metrics["bookings_today"] == 0
        assert metrics["bookings_week"] == 0
        assert metrics["revenue_estimate"] == 0.0
        assert metrics["avg_call_duration"] == 0.0
        assert metrics["satisfaction_score"] == 100.0

    def test_counts_calls_created_today(self, db: Session, sample_clinic):
        # Create 3 calls today
        now = datetime.now(timezone.utc)
        for _ in range(3):
            create_test_call(db, sample_clinic.id, created_at=now)
        db.commit()

        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        assert metrics["calls_today"] == 3
        assert metrics["calls_week"] == 3
        assert metrics["calls_month"] == 3

    def test_does_not_count_old_calls_same_month(self, db: Session, sample_clinic):
        """Calls from last month should not appear in today/week/month counts
        if today is in a different calendar month."""
        old = datetime.now(timezone.utc) - timedelta(days=60)
        create_test_call(db, sample_clinic.id, created_at=old)
        db.commit()

        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        assert metrics["calls_today"] == 0
        assert metrics["calls_week"] == 0
        assert metrics["calls_month"] == 0

    def test_bookings_today_excludes_cancelled(self, db: Session, sample_clinic):
        now = datetime.now(timezone.utc)
        create_test_appointment(db, sample_clinic.id, datetime_obj=now, status="scheduled")
        create_test_appointment(db, sample_clinic.id, datetime_obj=now, status="cancelled")
        db.commit()

        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        assert metrics["bookings_today"] == 1

    def test_avg_call_duration(self, db: Session, sample_clinic):
        create_test_call(db, sample_clinic.id, duration_seconds=120)
        create_test_call(db, sample_clinic.id, duration_seconds=180)
        db.commit()

        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        assert metrics["avg_call_duration"] == 150.0

    def test_satisfaction_score_percentage(self, db: Session, sample_clinic):
        create_test_call(db, sample_clinic.id, sentiment="positive")
        create_test_call(db, sample_clinic.id, sentiment="positive")
        create_test_call(db, sample_clinic.id, sentiment="neutral")
        create_test_call(db, sample_clinic.id, sentiment="negative")
        db.commit()

        metrics = AnalyticsService.get_dashboard_metrics(sample_clinic.id, db)
        # 2 positive out of 4 = 50%
        assert metrics["satisfaction_score"] == 50.0


class TestTimeSeries:
    """Daily aggregation for charts."""

    def test_calls_over_time_fills_gaps(self, db: Session, sample_clinic):
        """Days without calls should show 0 in the time-series."""
        series = AnalyticsService.get_calls_over_time(sample_clinic.id, days=7, db=db)
        assert len(series) == 8  # today + 7 past days = 8 entries
        for entry in series:
            assert "date" in entry
            assert "count" in entry
            assert entry["count"] >= 0

    def test_bookings_over_time_excludes_cancelled(self, db: Session, sample_clinic):
        now = datetime.now(timezone.utc)
        create_test_appointment(db, sample_clinic.id, datetime_obj=now, status="scheduled")
        create_test_appointment(db, sample_clinic.id, datetime_obj=now, status="cancelled")
        db.commit()

        series = AnalyticsService.get_bookings_over_time(sample_clinic.id, days=7, db=db)
        assert len(series) == 8
        # Today should show 1 booking (not the cancelled one)
        today_str = str(datetime.now(timezone.utc).date())
        today_entry = [e for e in series if e["date"] == today_str]
        assert len(today_entry) == 1
        assert today_entry[0]["count"] == 1


class TestTopServices:
    """Ranked service query."""

    def test_returns_empty_for_no_appointments(self, db: Session, sample_clinic):
        services = AnalyticsService.get_top_services(sample_clinic.id, db)
        assert services == []

    def test_ranks_services_by_count(self, db: Session, sample_clinic):
        create_test_appointment(db, sample_clinic.id, service_type="Cleaning")
        create_test_appointment(db, sample_clinic.id, service_type="Cleaning")
        create_test_appointment(db, sample_clinic.id, service_type="Cleaning")
        create_test_appointment(db, sample_clinic.id, service_type="Implant")
        create_test_appointment(db, sample_clinic.id, service_type="Whitening")
        db.commit()

        services = AnalyticsService.get_top_services(sample_clinic.id, db)
        assert len(services) == 3
        # Most booked first
        assert services[0]["service"] == "Cleaning"
        assert services[0]["count"] == 3


class TestLanguageStats:
    """Language breakdown."""

    def test_counts_en_and_es(self, db: Session, sample_clinic):
        create_test_call(db, sample_clinic.id, language="en")
        create_test_call(db, sample_clinic.id, language="en")
        create_test_call(db, sample_clinic.id, language="es")
        db.commit()

        stats = AnalyticsService.get_language_stats(sample_clinic.id, db)
        assert stats["en"] == 2
        assert stats["es"] == 1

    def test_defaults_null_to_en(self, db: Session, sample_clinic):
        call = create_test_call(db, sample_clinic.id, language="en")
        call.language = None
        db.commit()

        stats = AnalyticsService.get_language_stats(sample_clinic.id, db)
        assert stats["en"] == 1
