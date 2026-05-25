"""
Tests for backend/api/appointments.py — CRUD, availability, book-from-call.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.appointment import Appointment
from tests.conftest import create_auth_headers, create_test_appointment


class TestListAppointments:
    """GET /api/v1/appointments/"""

    def test_returns_empty_list(self, client: TestClient, sample_user):
        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/appointments/", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_clinic_appointments(self, client: TestClient, db: Session, sample_user, sample_clinic):
        create_test_appointment(db, sample_clinic.id)
        create_test_appointment(db, sample_clinic.id)
        db.commit()

        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/appointments/", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_filters_by_status(self, client: TestClient, db: Session, sample_user, sample_clinic):
        create_test_appointment(db, sample_clinic.id, status="scheduled")
        create_test_appointment(db, sample_clinic.id, status="cancelled")
        db.commit()

        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/appointments/?status=cancelled", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "cancelled"

    def test_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/appointments/")
        assert response.status_code == 401


class TestCreateAppointment:
    """POST /api/v1/appointments/"""

    def test_creates_appointment(self, client: TestClient, db: Session, sample_user, sample_clinic):
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        headers = create_auth_headers(sample_user)
        response = client.post("/api/v1/appointments/", headers=headers, json={
            "appointment_datetime": future,
            "duration_minutes": 30,
            "service_type": "Dental Cleaning",
            "notes": "Prefers morning",
        })
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["service_type"] == "Dental Cleaning"
        assert data["status"] == "scheduled"

        # Verify database
        appt = db.query(Appointment).filter(Appointment.id == data["id"]).first()
        assert appt is not None
        assert appt.notes == "Prefers morning"

    def test_invalid_patient_id_rejected(self, client: TestClient, sample_user):
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        headers = create_auth_headers(sample_user)
        response = client.post("/api/v1/appointments/", headers=headers, json={
            "patient_id": "nonexistent-id",
            "appointment_datetime": future,
            "service_type": "Checkup",
        })
        assert response.status_code == 404
        assert "patient" in response.json()["detail"].lower()


class TestUpdateAppointment:
    """PUT /api/v1/appointments/{id}"""

    def test_updates_fields(self, client: TestClient, db: Session, sample_user, sample_clinic):
        appt = create_test_appointment(db, sample_clinic.id, service_type="Old Service")

        headers = create_auth_headers(sample_user)
        response = client.put(f"/api/v1/appointments/{appt.id}", headers=headers, json={
            "service_type": "New Service",
            "notes": "Updated note",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["service_type"] == "New Service"
        assert data["notes"] == "Updated note"

    def test_404_for_nonexistent(self, client: TestClient, sample_user):
        headers = create_auth_headers(sample_user)
        response = client.put("/api/v1/appointments/nonexistent-id", headers=headers, json={
            "service_type": "X",
        })
        assert response.status_code == 404


class TestCancelAppointment:
    """DELETE /api/v1/appointments/{id}"""

    def test_sets_status_to_cancelled(self, client: TestClient, db: Session, sample_user, sample_clinic):
        appt = create_test_appointment(db, sample_clinic.id, status="scheduled")

        headers = create_auth_headers(sample_user)
        response = client.delete(f"/api/v1/appointments/{appt.id}", headers=headers)
        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

        db.refresh(appt)
        assert appt.status == "cancelled"

    def test_404_for_nonexistent(self, client: TestClient, sample_user):
        headers = create_auth_headers(sample_user)
        response = client.delete("/api/v1/appointments/nonexistent-id", headers=headers)
        assert response.status_code == 404


class TestTodayAppointments:
    """GET /api/v1/appointments/today"""

    def test_returns_todays_appointments(self, client: TestClient, db: Session, sample_user, sample_clinic):
        from backend.utils.timezone import get_florida_now

        now = get_florida_now()
        create_test_appointment(db, sample_clinic.id, datetime_obj=now, status="scheduled")

        # Create one in the past and one in the future — both should be excluded
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        create_test_appointment(db, sample_clinic.id, datetime_obj=yesterday)
        create_test_appointment(db, sample_clinic.id, datetime_obj=tomorrow)
        db.commit()

        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/appointments/today", headers=headers)
        assert response.status_code == 200
        # Only today's appointment should be returned
        data = response.json()
        assert len(data) == 1


class TestAvailability:
    """GET /api/v1/appointments/availability"""

    def test_requires_date_param(self, client: TestClient, sample_user):
        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/appointments/availability", headers=headers)
        assert response.status_code == 422  # Missing required query param

    def test_excludes_booked_slots(self, client: TestClient, db: Session, sample_user, sample_clinic):
        """Slots that have appointments should be excluded from availability."""
        from backend.utils.timezone import FL_TZ

        # Book a slot at 10:00 AM on a future date
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        future_local = future_date.astimezone(FL_TZ)
        booked_time = future_local.replace(hour=10, minute=0, second=0, microsecond=0)
        create_test_appointment(db, sample_clinic.id, datetime_obj=booked_time)
        db.commit()

        date_str = future_local.strftime("%Y-%m-%d")
        headers = create_auth_headers(sample_user)
        response = client.get(f"/api/v1/appointments/availability?date={date_str}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # The 10:00 slot should NOT be in the available slots
        slots = data.get("slots", [])
        slot_starts = [s["start"] for s in slots]
        assert "10:00" not in slot_starts
