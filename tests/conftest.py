"""
GrokDent FL — Shared Test Fixtures

Provides:
- In-memory SQLite database with tables created per test session
- FastAPI TestClient with app and dependency override for DB sessions
- Auth helpers (create_access_token, auth_headers)
- Factory helpers for clinics, users, patients, appointments
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt

# Ensure backend is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Base, get_db
from backend.config import settings
from backend.main import app
from backend.models.clinic import Clinic
from backend.models.user import User
from backend.models.patient import Patient
from backend.models.appointment import Appointment
from backend.models.call_log import CallLog

# ── Password hashing ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Test database (in-memory SQLite, fast and isolated) ─────────────────────
TEST_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Pytest fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session.

    NOTE: scope="session" means tables are created once. If a future test
    modifies table structure (DDL), other tests won't see the change.
    For schema-modifying tests, use a function-scoped fixture instead.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    """Provide a clean database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """FastAPI TestClient with DB dependency overridden."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Factory helpers ─────────────────────────────────────────────────────────

@pytest.fixture()
def sample_clinic(db: Session) -> Clinic:
    """Create and return a sample clinic."""
    clinic = Clinic(
        id=str(uuid.uuid4()),
        name="Sunshine Smiles Dental",
        slug="sunshine-smiles-dental",
        state="FL",
        timezone="US/Eastern",
        phone="407-555-0100",
        city="Orlando",
        zip_code="32801",
        is_active=True,
        hours={
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "18:00"},
            "friday": {"open": "08:00", "close": "16:00"},
            "saturday": {"open": "09:00", "close": "14:00"},
        },
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return clinic


@pytest.fixture()
def sample_user(db: Session, sample_clinic: Clinic) -> User:
    """Create an admin user in the sample clinic."""
    hashed = pwd_context.hash("password123")
    user = User(
        id=str(uuid.uuid4()),
        clinic_id=sample_clinic.id,
        email="admin@sunshinesmiles.com",
        hashed_password=hashed,
        full_name="Dr. Priya Patel",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sample_patient(db: Session, sample_clinic: Clinic) -> Patient:
    """Create a sample patient."""
    patient = Patient(
        id=str(uuid.uuid4()),
        clinic_id=sample_clinic.id,
        first_name="Maria",
        last_name="Garcia",
        phone_encrypted="encrypted_mock_phone",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def create_auth_headers(user: User) -> dict:
    """Return an Authorization header dict for the given user."""
    token = jwt.encode(
        {"sub": user.id, "clinic_id": user.clinic_id, "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_appointment(
    db: Session,
    clinic_id: str,
    patient_id: str | None = None,
    datetime_obj: datetime | None = None,
    service_type: str = "General Checkup",
    status: str = "scheduled",
) -> Appointment:
    """Quick helper to create an appointment."""
    if datetime_obj is None:
        datetime_obj = datetime.now(timezone.utc) + timedelta(days=3)
    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_datetime=datetime_obj,
        duration_minutes=30,
        service_type=service_type,
        status=status,
        created_via="test",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def create_test_call(
    db: Session,
    clinic_id: str,
    duration_seconds: int = 180,
    sentiment: str = "positive",
    language: str = "en",
    created_at: datetime | None = None,
) -> CallLog:
    """Quick helper to create a call log entry."""
    call = CallLog(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        twilio_call_sid=f"CA_test_{uuid.uuid4().hex[:16]}",
        caller_number="+14075551234",
        duration_seconds=duration_seconds,
        sentiment=sentiment,
        language=language,
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call
