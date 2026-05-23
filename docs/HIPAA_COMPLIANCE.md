# HIPAA Compliance & Security Framework for GrokDent FL

This document details the HIPAA (Health Insurance Portability and Accountability Act) security, privacy, and compliance safeguards implemented within the GrokDent FL voice receptionist and dashboard SaaS platform. It serves as an audit-ready guide for practice administrators and technical compliance officers.

---

## 1. Compliance Architecture Overview

GrokDent FL processes, transmits, and stores Protected Health Information (PHI) and electronic PHI (ePHI) on behalf of covered entities (dental clinics in Florida). To comply with the HIPAA Security Rule (45 CFR Part 160 and Part 164, Subparts A and C), we implement a multi-layered security framework spanning **Technical, Administrative, and Physical Safeguards**.

```
                         +-----------------------------------+
                         |      Covered Entity (Clinic)      |
                         +-----------------+-----------------+
                                           |  Signed BAA
                                           v
                         +-----------------+-----------------+
                         |      GrokDent FL SaaS Engine      |
                         +--------+-----------------+--------+
                                  |                 |
         +------------------------+                 +------------------------+
         | AES-256 App Encryption                   | TLS 1.3 Transmission   |
         v                                          v                        v
+--------+--------+                         +-------+-------+       +--------+--------+
|   PostgreSQL    |                         |  Twilio Voice |       | xAI Grok Voice  |
|  (ePHI At Rest) |                         |   (Telephony) |       | (Bilingual AI)  |
+-----------------+                         +---------------+       +-----------------+
```

---

## 2. Technical Safeguards (164.312)

### A. Transmission Security (164.312(e))
- **TLS 1.3 Encryption**: All API calls between the browser dashboard and the FastAPI backend, and webhooks from Twilio, are encrypted using Transport Layer Security (TLS 1.3) with strong cipher suites. Older SSL versions and weak TLS configurations are disabled.
- **Secure WebSockets (WSS)**: Real-time dashboard communications use encrypted WebSockets (`wss://`) to prevent eavesdropping on live call events.

### B. Application-Layer Field Encryption (164.312(a)(2)(iv))
To protect patient identities and clinical information even in the event of an underlying database breach, GrokDent FL implements **AES-256 field-level encryption** using the standard Fernet symmetric key formulation.
- **Symmetric Keys**: Encryption keys are derived from a high-entropy `ENCRYPTION_KEY` environment variable that must be set in production.
- **Encrypted Patient Columns**:
  - `phone_encrypted`
  - `email_encrypted`
  - `dob_encrypted`
  - `insurance_id_encrypted`
  - `notes_encrypted`
- **Encrypted System Logs**:
  - `CallLog.transcript_encrypted`
  - `CallLog.recording_url_encrypted`

### C. Unique User Authentication & Access Control (164.312(a))
- **Secure Hashing**: User passwords are encrypted using `bcrypt` with a high workload factor before storage. Plaintext passwords are never logged, stored, or transmitted.
- **JSON Web Tokens (JWT)**: Authentication is maintained using signed JWT access tokens with a standard 30-minute expiration period.
- **Role-Based Access Control (RBAC)**:
  - `admin`: Full practice configuration, billing, billing cancellations, user management, and complete patient records access.
  - `manager` / `staff`: Patient lookups, appointment schedules, and call logs. Restricted from deleting clinical logs or changing clinic settings.

### D. Audit Controls & Log Maintenance (164.312(b))
The `HIPAAAuditMiddleware` intercepts all incoming API requests (excluding basic health checks and public static UI elements) and records immutable audit entries in the `audit_logs` table:
- **Timestamp**: Exact UTC date and time.
- **User Identifier**: The JWT user ID and email who performed the action.
- **IP Address & Browser User-Agent**: Records the source machine and connection metadata.
- **Action Type**: Classified as `view` (GET), `create` (POST), `update` (PUT/PATCH), or `delete` (DELETE).
- **Target Resource**: The specific URI path and queried resource identifier.

---

## 3. Florida-Specific Consent Requirements

### Florida Wiretap Law & Two-Party Consent (§ 934.03, Fla. Stat.)
Florida is a **two-party consent state** (often referred to as all-party consent). It is a third-degree felony to record a wire, oral, or electronic communication unless all parties involved have consented to the recording beforehand.

#### GrokDent FL Compliance Protocol
To satisfy § 934.03, GrokDent FL embeds a mandatory audio disclosure at the very beginning of every inbound and outbound telephone call. The voice agent must play the following greeting prior to recording or parsing speech gather commands:

> "Thank you for calling Sunshine Smiles Dental. Just so you know, I am an AI dental assistant and this call may be recorded for quality purposes. How can I help you today?"

If the patient continues the conversation after this announcement, their consent to be recorded is legally implied under Florida case law. If the clinic disables call recording, this warning can be dynamically adjusted, but it is highly recommended to keep it enabled for liability protection.

---

## 4. Business Associate Agreements (BAAs)

Under HIPAA, any vendor that touches, stores, or processes ePHI is a **Business Associate** and must execute a formal **Business Associate Agreement (BAA)**.

### Mandatory Vendor BAA Checklist:
1. **Cloud Hosting Provider** (e.g., AWS, Railway, Heroku): Must be configured under an enterprise account with a signed BAA ensuring physical isolation and DB encryption.
2. **Telephony Carrier** (Twilio): Must sign a BAA. Ensure Twilio's "HIPAA-Eligible" voice services are enabled, which automatically routes media through secure media links and restricts long-term recording storage on Twilio servers.
3. **AI Reasoning Provider** (xAI Grok): Ensure you are using xAI's developer API under a commercial tier which legally guarantees that inputs/prompts are not utilized to train future public LLM models, and request a BAA for enterprise workloads.

---

## 5. Security & Administrative Checklist

| Category | Requirement | Implementation Status | GrokDent FL Control |
|---|---|---|---|
| **Technical** | Access Authorization | `[ COMPLETED ]` | JWT validation & RBAC roles |
| **Technical** | Audit Controls | `[ COMPLETED ]` | `HIPAAAuditMiddleware` logs |
| **Technical** | PHI Encryption | `[ COMPLETED ]` | Fernet AES-256 encryption service |
| **Technical** | Automatic Logoff | `[ COMPLETED ]` | 30-minute JWT token expiration |
| **Administrative**| Risk Assessment | `[ PENDING ]` | Must be conducted annually by the clinic |
| **Administrative**| BAA Signatures | `[ PENDING ]` | Clinic must execute BAAs with Twilio & AWS |
| **Physical** | Device Security | `[ PENDING ]` | Use HTTPS/WSS, secure local clinic terminals |
