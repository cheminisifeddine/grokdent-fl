"""
Tests for backend/api/auth.py — signup, login, token validation, /me endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.user import User
from tests.conftest import create_auth_headers


class TestSignup:
    """POST /api/v1/auth/signup"""

    def test_signup_creates_user_and_returns_token(self, client: TestClient, db: Session):
        response = client.post("/api/v1/auth/signup", json={
            "clinic_name": "Test Dental",
            "email": "dentist@testdental.com",
            "password": "securePassword123",
            "full_name": "Dr. Tester",
        })
        assert response.status_code == 201, response.text
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["email"] == "dentist@testdental.com"
        assert data["user"]["role"] == "admin"

        # Verify database state
        user = db.query(User).filter(User.email == "dentist@testdental.com").first()
        assert user is not None
        assert user.full_name == "Dr. Tester"

    def test_signup_duplicate_email_rejected(self, client: TestClient, db: Session):
        client.post("/api/v1/auth/signup", json={
            "clinic_name": "First Clinic",
            "email": "dupe@test.com",
            "password": "password123456",
            "full_name": "First User",
        })
        response = client.post("/api/v1/auth/signup", json={
            "clinic_name": "Second Clinic",
            "email": "dupe@test.com",
            "password": "password123456",
            "full_name": "Second User",
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_short_password_rejected(self, client: TestClient):
        response = client.post("/api/v1/auth/signup", json={
            "clinic_name": "Test Dental",
            "email": "shortpw@test.com",
            "password": "12345",
            "full_name": "Short PW",
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_signup_invalid_email_rejected(self, client: TestClient):
        response = client.post("/api/v1/auth/signup", json={
            "clinic_name": "Test",
            "email": "not-an-email",
            "password": "password123456",
            "full_name": "Bad Email",
        })
        assert response.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    def test_login_valid_credentials(self, client: TestClient, db: Session, sample_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@sunshinesmiles.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@sunshinesmiles.com"

    def test_login_wrong_password(self, client: TestClient, sample_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@sunshinesmiles.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "password123",
        })
        assert response.status_code == 401

    def test_login_updates_last_login(self, client: TestClient, db: Session, sample_user):
        old_login = sample_user.last_login
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@sunshinesmiles.com",
            "password": "password123",
        })
        assert response.status_code == 200
        db.refresh(sample_user)
        assert sample_user.last_login is not None
        if old_login:
            assert sample_user.last_login >= old_login

    def test_login_inactive_user(self, client: TestClient, db: Session, sample_user):
        sample_user.is_active = False
        db.commit()
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@sunshinesmiles.com",
            "password": "password123",
        })
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


class TestGetMe:
    """GET /api/v1/auth/me"""

    def test_returns_current_user(self, client: TestClient, sample_user):
        headers = create_auth_headers(sample_user)
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@sunshinesmiles.com"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    def test_no_token_returns_401(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
        assert response.status_code == 401
