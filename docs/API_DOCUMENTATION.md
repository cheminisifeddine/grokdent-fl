# GrokDent FL — API Reference Documentation

This document provides a comprehensive API reference for the GrokDent FL backend services. All REST requests must be sent over HTTPS. Standard API payloads utilize the JSON specification.

---

## 1. Authentication (JWT)

Unless marked as public webhooks, all endpoints require authentication using a JSON Web Token (JWT) supplied as a Bearer token in the `Authorization` header.

```http
Authorization: Bearer <your_jwt_access_token>
```

Tokens are obtained via the `/api/v1/auth/login` or `/api/v1/auth/signup` endpoints. They are signed using HMAC-SHA256 and expire after **30 minutes**.

---

## 2. API Endpoints Reference

### 🔐 Authentication Router (`/api/v1/auth`)

#### `POST /signup` (Public)
Creates a new dental clinic profile and registers the first administrator user. Returns a JWT access token.

- **Request Body**:
  ```json
  {
    "clinic_name": "Smile Dental FL",
    "email": "dr.smith@smiledental.com",
    "password": "production_secure_pass_123",
    "full_name": "Dr. John Smith"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "e4b3c9a1-62bc-4402-861f-149bde965ad4",
      "clinic_id": "8bfa2e9a-7c2a-4df1-8e01-cc8742b78119",
      "email": "dr.smith@smiledental.com",
      "full_name": "Dr. John Smith",
      "role": "admin",
      "is_active": true
    }
  }
  ```

#### `POST /login` (Public)
Authenticates credentials and returns a JWT access token.

- **Request Body**:
  ```json
  {
    "email": "dr.smith@smiledental.com",
    "password": "production_secure_pass_123"
  }
  ```
- **Response (200 OK)**: (Same structure as `/signup` response)

---

### 🏥 Clinics Router (`/api/v1/clinics`)

#### `GET /` (Auth Required)
Fetches the profile metadata for the authenticated user's clinic.

- **Response (200 OK)**:
  ```json
  {
    "id": "8bfa2e9a-7c2a-4df1-8e01-cc8742b78119",
    "name": "Sunshine Smiles Dental",
    "slug": "sunshine-smiles-dental",
    "phone": "(407) 555-0100",
    "email": "info@sunshinesmilesdental.com",
    "address": "1234 Orange Blossom Trail",
    "city": "Orlando",
    "state": "FL",
    "zip_code": "32801",
    "timezone": "US/Eastern",
    "services": ["General Dentistry", "Cosmetic Dentistry"],
    "hours": {
      "monday": {"open": "08:00", "close": "17:00"}
    },
    "insurance_accepted": ["Delta Dental", "Cigna"],
    "emergency_contact_name": "Dr. Priya Patel",
    "emergency_contact_phone": "(407) 555-0199",
    "grok_voice_id": "Ash",
    "twilio_phone_number": "+14075550100",
    "subscription_plan": "professional",
    "subscription_status": "active",
    "policies": "Cancellation policy details...",
    "welcome_message": "Welcome message text...",
    "spanish_enabled": true
  }
  ```

---

### 📅 Appointments Router (`/api/v1/appointments`)

#### `GET /` (Auth Required)
Lists all appointments for the clinic. Supports date range filters.

- **Query Parameters**:
  - `date_from` (Optional, `YYYY-MM-DD`)
  - `date_to` (Optional, `YYYY-MM-DD`)
  - `status` (Optional, e.g., `scheduled`, `confirmed`, `cancelled`)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "a902b1c4-54fd-4df1-8e2b-ffbc98e1f0e4",
      "clinic_id": "8bfa2e9a-7c2a-4df1-8e01-cc8742b78119",
      "patient_id": "67cb1a4b-9e12-4211-9a7c-ec8efd920141",
      "appointment_datetime": "2026-05-25T14:00:00Z",
      "duration_minutes": 30,
      "service_type": "Adult Cleaning",
      "status": "confirmed",
      "notes": "Routine recall cleaning.",
      "google_calendar_event_id": "gcal_event_abc123",
      "created_via": "web_dashboard"
    }
  ]
  ```

#### `POST /book-from-call` (Public / Internal)
Allows the stateful AI receptionist to insert new appointments into the timeline. Auto-creates patients if they are new.

- **Request Body**:
  ```json
  {
    "patient_name": "Sarah Connor",
    "phone": "+13055550999",
    "service": "Composite Filling (1 surface)",
    "preferred_time": "2026-05-26T10:00:00Z",
    "duration_minutes": 30,
    "language": "en"
  }
  ```

---

### 👤 Patients Router (`/api/v1/patients`)

#### `GET /` (Auth Required)
Returns paginated patient lists. Encrypted clinical/PII database columns are decrypted on the fly before response.

- **Response (200 OK)**:
  ```json
  [
    {
      "id": "67cb1a4b-9e12-4211-9a7c-ec8efd920141",
      "clinic_id": "8bfa2e9a-7c2a-4df1-8e01-cc8742b78119",
      "first_name": "Sarah",
      "last_name": "Connor",
      "phone": "(305) 555-0999",
      "email": "sarah.connor@sky.net",
      "dob": "1965-11-10",
      "insurance_provider": "Delta Dental of Florida",
      "insurance_id": "DD9998811",
      "preferred_language": "en",
      "notes": "Prefers evening appointments.",
      "created_at": "2026-05-20T10:00:00Z",
      "updated_at": "2026-05-20T10:00:00Z"
    }
  ]
  ```

#### `GET /search` (Auth Required)
Searches patients by name, phone, or email.

- **Query Parameters**:
  - `q` (Required, Search query string)

---

### 📞 Call Logs Router (`/api/v1/calls`)

#### `GET /` (Auth Required)
Fetches Call Logs. AES-encrypted conversation transcripts are decrypted automatically.

- **Response (200 OK)**:
  ```json
  [
    {
      "id": "c1f7b9e0-d3cb-4af1-bf31-ee9201e51b14",
      "clinic_id": "8bfa2e9a-7c2a-4df1-8e01-cc8742b78119",
      "patient_id": "67cb1a4b-9e12-4211-9a7c-ec8efd920141",
      "twilio_call_sid": "CA112233445566778899aabbccddeeff",
      "direction": "inbound",
      "caller_number": "+13055550999",
      "called_number": "+14075550100",
      "duration_seconds": 120,
      "status": "completed",
      "transcript": "AI: How can I help you?\nUSER: I need to book a filling...",
      "summary": "Patient booked a filling appointment.",
      "sentiment": "positive",
      "language": "en",
      "actions_taken": ["book_appointment"],
      "is_emergency": false,
      "created_at": "2026-05-20T10:05:00Z"
    }
  ]
  ```

---

## 3. Real-Time WebSocket API

Provides instant UI alerts and live status logs to the browser dashboard when call actions occur.

- **WebSocket URL**:
  `wss://yourdomain.com/ws/{clinic_id}`

### Pushed Event Structures:
```json
{
  "event": "call_started",
  "timestamp": 1782390112,
  "data": {
    "call_sid": "CA11223344...",
    "caller": "+13055550999",
    "language": "en"
  }
}
```
```json
{
  "event": "appointment_booked",
  "timestamp": 1782390235,
  "data": {
    "id": "a902b1c4-54fd-4df1...",
    "patient_name": "Sarah Connor",
    "service_type": "Composite Filling (1 surface)",
    "time": "2026-05-26T10:00:00Z"
  }
}
```

---

## 4. API Response Error Codes

| HTTP Status | Detail Message | Explanation / Remediation |
|---|---|---|
| `400 Bad Request` | "Email already registered" | Check if the signup email is duplicate. |
| `401 Unauthorized`| "Invalid or expired token" | Supply a fresh Bearer JWT in the Authorization header. |
| `403 Forbidden`   | "Account is deactivated" | The clinic subscription has been closed. |
| `404 Not Found`   | "Appointment not found" | Resource does not exist or belongs to another clinic. |
| `422 Unprocessable`| (ValidationError payload) | Field validations failed. Check date/email formats. |
| `500 Server Error`| "Internal analytics error" | The DB connection failed or calculations faulted. |
