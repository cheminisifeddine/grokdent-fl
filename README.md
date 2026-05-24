# 🦷 Renia AI — AI Voice Receptionist for Florida Dental Clinics

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-brightgreen.svg)](docs/HIPAA_COMPLIANCE.md)
[![Deployment](https://img.shields.io/badge/Deploy-Docker%20%7C%20AWS%20%7C%20Railway-orange.svg)](docs/DEPLOYMENT_GUIDE.md)

---

## Overview

**Renia AI** is a full-stack SaaS platform providing AI-powered voice receptionist services exclusively for dental clinics in Florida. Built on xAI's Grok large language model and integrated with Twilio's programmable voice platform, Renia AI answers every incoming call 24/7 with a natural, conversational AI agent that can book appointments, verify insurance, route emergencies, and answer patient questions — in both English and Spanish.

Florida's 12,000+ dental practices lose an estimated 30% of incoming calls to hold times, voicemail, and after-hours unavailability. Each missed call represents $200–$500 in lost revenue. Renia AI eliminates this problem entirely by ensuring every call is answered instantly, every patient is heard, and every appointment opportunity is captured.

The platform is **HIPAA-compliant by design**, with AES-256 encryption at rest, TLS 1.3 in transit, comprehensive audit trails, role-based access control, and Business Associate Agreements with all third-party vendors. Florida's two-party consent recording law (§934.03) is handled automatically with configurable disclosure scripts.

---

## Features

### 🎙️ AI Voice Receptionist
- **24/7 AI-powered call answering** — powered by xAI Grok with dental-specific fine-tuning
- **Natural, interruptible conversations** — patients can interrupt, change topics, or ask follow-up questions naturally
- **English ↔ Spanish bilingual support** — automatic language detection with seamless switching
- **Configurable voice personas** — adjust tone, pace, and personality per clinic brand
- **Emergency triage & routing** — recognizes dental emergencies and routes to on-call dentists immediately

### 📅 Appointment Management
- **Smart scheduling** — books, cancels, and reschedules appointments with real-time availability checking
- **Google Calendar sync** — bidirectional sync with existing clinic calendars
- **Provider matching** — routes patients to the correct dentist based on procedure type
- **Waitlist management** — fills cancellations automatically from the waitlist
- **SMS/email confirmations** — instant booking confirmations and reminders via SendGrid

### 🏥 Patient Services
- **Insurance verification** — validates insurance plans and coverage in real-time
- **New patient intake** — collects demographics, insurance, and medical history over the phone
- **Knowledge base Q&A** — answers common questions about services, hours, directions, pricing
- **Multi-location support** — handles calls for clinic groups with multiple offices

### 📊 Analytics & Management
- **Real-time analytics dashboard** — call volumes, booking rates, peak hours, sentiment analysis
- **Call transcription & recording** — searchable transcripts with AI-generated summaries
- **Stripe billing integration** — automated subscription management with usage-based add-ons
- **Role-based access control** — Owner, Admin, Staff, and Read-Only roles
- **HIPAA-compliant audit trails** — every action logged with timestamp, user, and IP address

---

## Quick Start

### Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **PostgreSQL 15+** — [Download](https://www.postgresql.org/download/)
- **Redis 7+** — [Download](https://redis.io/download/) (or use Docker)
- **Node.js 18+** (for frontend) — [Download](https://nodejs.org/)
- **Docker & Docker Compose** (recommended) — [Download](https://www.docker.com/products/docker-desktop/)

### Clone & Configure

```bash
git clone https://github.com/yourusername/renia-ai.git
cd renia-ai
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)
```

### Option A: Docker (Recommended)

```bash
# Build and start all services (backend, frontend, PostgreSQL, Redis)
docker-compose up --build

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed demo data
docker-compose exec backend python scripts/seed_data.py
```

### Option B: Manual Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed demo data (creates demo clinic, patients, appointments)
python scripts/seed_data.py

# Start the backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Option C: Frontend Development

```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:3000
```

### Access the Application

| Service | URL |
|---------|-----|
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Frontend Dashboard** | http://localhost:3000 |

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Super Admin** | admin@grokdentfl.com | password123 |
| **Clinic Owner** | admin@sunshinesmiles.com | password123 |
| **Staff** | sarah@sunshinesmiles.com | password123 |
| **Read-Only** | viewer@sunshinesmiles.com | password123 |

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Core Application

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `APP_NAME` | Application name | No | `Renia AI` | — |
| `APP_ENV` | Environment (`development`, `staging`, `production`) | Yes | `development` | — |
| `APP_DEBUG` | Enable debug mode | No | `true` | — |
| `APP_SECRET_KEY` | Secret key for JWT signing (min 32 chars) | Yes | — | Generate: `openssl rand -hex 32` |
| `APP_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `http://localhost:3000` | — |

### Database

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | — | `postgresql://user:pass@localhost:5432/grokdent` |
| `DATABASE_POOL_SIZE` | Connection pool size | No | `10` | — |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | No | `20` | — |
| `REDIS_URL` | Redis connection string | Yes | — | `redis://localhost:6379/0` |

### xAI (Grok)

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `XAI_API_KEY` | xAI API key for Grok access | Yes | — | [console.x.ai](https://console.x.ai) |
| `XAI_MODEL` | Grok model to use | No | `grok-3` | — |
| `XAI_MAX_TOKENS` | Max response tokens | No | `1024` | — |
| `XAI_TEMPERATURE` | Response creativity (0.0–1.0) | No | `0.3` | — |
| `XAI_TIMEOUT_SECONDS` | API timeout in seconds | No | `30` | — |

### Twilio

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes | — | [twilio.com/console](https://www.twilio.com/console) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes | — | [twilio.com/console](https://www.twilio.com/console) |
| `TWILIO_PHONE_NUMBER` | Twilio phone number (E.164 format) | Yes | — | [twilio.com/console/phone-numbers](https://www.twilio.com/console/phone-numbers) |
| `TWILIO_WEBHOOK_BASE_URL` | Public URL for Twilio webhooks | Yes | — | Your deployed domain or ngrok URL |
| `TWILIO_STATUS_CALLBACK_URL` | Call status callback URL | No | — | Auto-derived from webhook base URL |

### Google Calendar

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | Yes | — | [GCP Console](https://console.cloud.google.com/apis/credentials) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | Yes | — | [GCP Console](https://console.cloud.google.com/apis/credentials) |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI | No | `http://localhost:8000/api/v1/auth/google/callback` | — |

### Stripe

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `STRIPE_SECRET_KEY` | Stripe secret API key | Yes | — | [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Yes | — | [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | Yes | — | [dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks) |
| `STRIPE_STARTER_PRICE_ID` | Price ID for Starter tier ($299/mo) | Yes | — | Stripe Dashboard > Products |
| `STRIPE_PROFESSIONAL_PRICE_ID` | Price ID for Professional tier ($599/mo) | Yes | — | Stripe Dashboard > Products |
| `STRIPE_ENTERPRISE_PRICE_ID` | Price ID for Enterprise tier ($999/mo) | Yes | — | Stripe Dashboard > Products |

### SendGrid

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `SENDGRID_API_KEY` | SendGrid API key | Yes | — | [app.sendgrid.com/settings/api_keys](https://app.sendgrid.com/settings/api_keys) |
| `SENDGRID_FROM_EMAIL` | Verified sender email | Yes | — | Must be verified in SendGrid |
| `SENDGRID_FROM_NAME` | Sender display name | No | `Renia AI` | — |

### Security & Encryption

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `ENCRYPTION_KEY` | AES-256 encryption key for PHI | Yes | — | Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `JWT_ALGORITHM` | JWT signing algorithm | No | `HS256` | — |
| `JWT_EXPIRATION_MINUTES` | Access token expiry (minutes) | No | `30` | — |
| `JWT_REFRESH_EXPIRATION_DAYS` | Refresh token expiry (days) | No | `7` | — |

### Monitoring

| Variable | Description | Required | Default | Where to Get It |
|----------|-------------|----------|---------|-----------------|
| `SENTRY_DSN` | Sentry error tracking DSN | No | — | [sentry.io](https://sentry.io) |
| `LOG_LEVEL` | Logging level | No | `INFO` | — |
| `ENABLE_CALL_RECORDING` | Enable call recording | No | `false` | — |

---

## API Key Setup

### xAI (Grok)

1. Go to [https://console.x.ai](https://console.x.ai)
2. Create an account or sign in with your X (Twitter) account
3. Navigate to **API Keys** in the left sidebar
4. Click **"Create API Key"**
5. Name it `renia-ai-production` (or `renia-ai-dev` for development)
6. Copy the generated key immediately (it won't be shown again)
7. Add to your `.env` file:
   ```
   XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
8. **Billing**: Ensure you have a payment method on file. Renia AI uses approximately:
   - ~$0.002 per call (Grok API usage)
   - ~500–1,000 tokens per call interaction

### Twilio

1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio) and create an account
2. From the [Console Dashboard](https://www.twilio.com/console), copy your **Account SID** and **Auth Token**
3. Navigate to **Phone Numbers** → **Manage** → **Buy a Number**
4. Search for a number with:
   - **Country**: United States
   - **State/Region**: Florida
   - **Capabilities**: Voice ✅, SMS ✅
5. Purchase the number (starts at $1.15/month)
6. After purchasing, click the number to configure it:
   - **Voice & Fax** → **A Call Comes In** → **Webhook**
   - URL: `https://yourdomain.com/api/v1/webhooks/voice/incoming`
   - HTTP Method: `POST`
   - **Status Callback URL**: `https://yourdomain.com/api/v1/webhooks/voice/status`
7. For local development, use [ngrok](https://ngrok.com/) to expose your local server:
   ```bash
   ngrok http 8000
   # Use the ngrok URL as your webhook base URL
   ```
8. Add to your `.env` file:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_PHONE_NUMBER=+14075551234
   TWILIO_WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok-free.app
   ```

### Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named `renia-ai`
3. Enable the **Google Calendar API**:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Google Calendar API"
   - Click **Enable**
4. Create OAuth 2.0 credentials:
   - Navigate to **APIs & Services** → **Credentials**
   - Click **"Create Credentials"** → **"OAuth client ID"**
   - Application type: **Web application**
   - Name: `Renia AI`
   - Authorized redirect URIs: `http://localhost:8000/api/v1/auth/google/callback`
   - For production, add: `https://yourdomain.com/api/v1/auth/google/callback`
5. Copy the **Client ID** and **Client Secret**
6. Configure the OAuth consent screen:
   - Navigate to **OAuth consent screen**
   - User type: **External**
   - Add scopes: `https://www.googleapis.com/auth/calendar`
   - Add test users for development
7. Add to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxx
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
   ```

### Stripe

1. Go to [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register) and create an account
2. From the [Dashboard](https://dashboard.stripe.com/), toggle to **Test Mode** (top right) for development
3. Navigate to **Developers** → **API Keys**
4. Copy your **Publishable key** (`pk_test_...`) and **Secret key** (`sk_test_...`)
5. Create Products and Prices:
   - Go to **Products** → **Add Product**
   - Create three products:
     | Product | Price | Interval |
     |---------|-------|----------|
     | Renia AI Starter | $299.00 | Monthly |
     | Renia AI Professional | $599.00 | Monthly |
     | Renia AI Enterprise | $999.00 | Monthly |
   - Copy each **Price ID** (`price_...`)
6. Set up Webhooks:
   - Navigate to **Developers** → **Webhooks**
   - Click **"Add endpoint"**
   - URL: `https://yourdomain.com/api/v1/webhooks/stripe`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Copy the **Signing Secret** (`whsec_...`)
7. Add to your `.env` file:
   ```
   STRIPE_SECRET_KEY=your-stripe-test-secret-key-placeholder
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
   STRIPE_STARTER_PRICE_ID=price_xxxxxxxxxxxxxxxx
   STRIPE_PROFESSIONAL_PRICE_ID=price_xxxxxxxxxxxxxxxx
   STRIPE_ENTERPRISE_PRICE_ID=price_xxxxxxxxxxxxxxxx
   ```

### SendGrid

1. Go to [https://signup.sendgrid.com/](https://signup.sendgrid.com/) and create an account
2. Verify your email address
3. Navigate to **Settings** → **API Keys**
4. Click **"Create API Key"**
   - Name: `renia-ai`
   - Permissions: **Full Access** (or **Restricted Access** with Mail Send enabled)
5. Copy the generated API key (shown only once)
6. Set up Sender Verification:
   - Navigate to **Settings** → **Sender Authentication**
   - **Single Sender Verification**: Add and verify your sending email
   - **Domain Authentication** (recommended for production): Follow the DNS setup
7. Add to your `.env` file:
   ```
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   SENDGRID_FROM_EMAIL=noreply@grokdentfl.com
   SENDGRID_FROM_NAME=Renia AI
   ```

---

## Project Structure

```
renia-ai/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore rules
├── docker-compose.yml                 # Docker Compose orchestration
├── Dockerfile                         # Backend Docker image
├── Makefile                           # Common development commands
├── requirements.txt                   # Python dependencies
├── alembic.ini                        # Alembic migration configuration
├── pyproject.toml                     # Python project metadata
│
├── backend/                           # FastAPI backend application
│   ├── __init__.py
│   ├── main.py                        # Application entry point, lifespan events
│   ├── config.py                      # Settings management (Pydantic BaseSettings)
│   ├── database.py                    # Database engine, session factory
│   ├── dependencies.py                # FastAPI dependency injection
│   │
│   ├── models/                        # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                    # User, Role, Permission models
│   │   ├── clinic.py                  # Clinic, ClinicSettings models
│   │   ├── patient.py                 # Patient, InsuranceInfo models
│   │   ├── appointment.py             # Appointment, AppointmentSlot models
│   │   ├── call.py                    # Call, CallTranscript, CallEvent models
│   │   ├── knowledge_base.py          # KnowledgeBase, FAQ models
│   │   ├── billing.py                 # Subscription, Invoice, Payment models
│   │   └── audit_log.py              # AuditLog model for HIPAA compliance
│   │
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py                    # Login, Signup, Token schemas
│   │   ├── clinic.py                  # Clinic CRUD schemas
│   │   ├── patient.py                 # Patient CRUD schemas
│   │   ├── appointment.py             # Appointment CRUD, availability schemas
│   │   ├── call.py                    # Call log, transcript schemas
│   │   ├── knowledge_base.py          # KB entry schemas
│   │   ├── analytics.py              # Dashboard, time series schemas
│   │   └── billing.py                # Subscription, checkout schemas
│   │
│   ├── routers/                       # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                    # /api/v1/auth/*
│   │   ├── clinics.py                 # /api/v1/clinics/*
│   │   ├── patients.py                # /api/v1/patients/*
│   │   ├── appointments.py            # /api/v1/appointments/*
│   │   ├── calls.py                   # /api/v1/calls/*
│   │   ├── knowledge_base.py          # /api/v1/knowledge-base/*
│   │   ├── analytics.py              # /api/v1/analytics/*
│   │   ├── billing.py                # /api/v1/billing/*
│   │   └── webhooks.py               # /api/v1/webhooks/* (Twilio, Stripe)
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_agent.py               # Grok AI conversation engine
│   │   ├── voice_handler.py           # Twilio voice call processing
│   │   ├── appointment_service.py     # Appointment booking logic
│   │   ├── patient_service.py         # Patient lookup and creation
│   │   ├── insurance_service.py       # Insurance verification
│   │   ├── calendar_service.py        # Google Calendar sync
│   │   ├── notification_service.py    # SMS/email notifications (SendGrid)
│   │   ├── billing_service.py         # Stripe subscription management
│   │   ├── analytics_service.py       # Dashboard data aggregation
│   │   ├── knowledge_service.py       # Knowledge base search
│   │   ├── audit_service.py           # HIPAA audit trail logging
│   │   └── encryption_service.py      # AES-256 PHI encryption/decryption
│   │
│   ├── middleware/                     # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── auth_middleware.py         # JWT validation middleware
│   │   ├── audit_middleware.py        # Request/response audit logging
│   │   ├── rate_limit_middleware.py   # Rate limiting (Redis-backed)
│   │   └── cors_middleware.py         # CORS configuration
│   │
│   └── utils/                         # Utility functions
│       ├── __init__.py
│       ├── security.py                # Password hashing, JWT creation
│       ├── validators.py              # Phone number, email validation
│       ├── formatters.py              # Date/time formatting helpers
│       └── constants.py               # Enums, dental procedure codes
│
├── frontend/                          # React/Next.js frontend
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── public/                        # Static assets
│   │   ├── logo.svg
│   │   └── favicon.ico
│   └── src/
│       ├── app/                       # Next.js App Router pages
│       │   ├── layout.tsx             # Root layout
│       │   ├── page.tsx               # Landing page
│       │   ├── login/                 # Login page
│       │   ├── dashboard/             # Main dashboard
│       │   ├── appointments/          # Appointment management
│       │   ├── patients/              # Patient directory
│       │   ├── calls/                 # Call history & transcripts
│       │   ├── analytics/             # Analytics & reports
│       │   ├── knowledge-base/        # Knowledge base editor
│       │   ├── settings/              # Clinic & account settings
│       │   └── billing/               # Subscription management
│       ├── components/                # Reusable UI components
│       │   ├── ui/                    # Base components (shadcn/ui)
│       │   ├── charts/               # Chart components (Recharts)
│       │   ├── forms/                # Form components
│       │   └── layout/               # Header, Sidebar, Footer
│       ├── lib/                       # Client utilities
│       │   ├── api.ts                 # API client (Axios)
│       │   ├── auth.ts               # Auth context & hooks
│       │   └── utils.ts              # Helper functions
│       └── types/                     # TypeScript type definitions
│           └── index.ts
│
├── migrations/                        # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                      # Migration files
│       ├── 001_initial_schema.py
│       ├── 002_add_knowledge_base.py
│       ├── 003_add_billing_tables.py
│       └── 004_add_audit_logs.py
│
├── scripts/                           # Utility scripts
│   ├── seed_data.py                   # Seed demo data
│   ├── generate_encryption_key.py     # Generate AES-256 key
│   ├── run_migrations.py             # Run Alembic migrations
│   ├── backup_database.py            # Database backup script
│   └── test_twilio_webhook.py        # Test Twilio webhook locally
│
├── tests/                             # Test suite
│   ├── conftest.py                    # Shared test fixtures
│   ├── test_auth.py                   # Authentication tests
│   ├── test_appointments.py           # Appointment CRUD tests
│   ├── test_ai_agent.py              # AI conversation tests
│   ├── test_voice_handler.py          # Twilio webhook tests
│   ├── test_billing.py               # Stripe integration tests
│   ├── test_encryption.py            # Encryption/decryption tests
│   └── test_hipaa_compliance.py       # HIPAA compliance tests
│
└── docs/                              # Documentation
    ├── BUSINESS_PLAN.md               # Investor-ready business plan
    ├── HIPAA_COMPLIANCE.md            # HIPAA compliance guide
    ├── DEPLOYMENT_GUIDE.md            # Deployment instructions
    └── API_DOCUMENTATION.md           # Full API reference
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/auth/signup` | Register new clinic account | No |
| `POST` | `/api/v1/auth/login` | Login and get JWT token | No |
| `GET` | `/api/v1/auth/me` | Get current user profile | Yes |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Yes |
| `POST` | `/api/v1/auth/logout` | Invalidate refresh token | Yes |
| `GET` | `/api/v1/auth/google/callback` | Google OAuth callback | No |

### Clinics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/clinics` | Create new clinic | Yes (Admin) |
| `GET` | `/api/v1/clinics` | List all clinics | Yes (Admin) |
| `GET` | `/api/v1/clinics/{id}` | Get clinic details | Yes |
| `PUT` | `/api/v1/clinics/{id}` | Update clinic info | Yes (Owner) |
| `DELETE` | `/api/v1/clinics/{id}` | Delete clinic | Yes (Admin) |
| `PUT` | `/api/v1/clinics/{id}/settings` | Update clinic settings | Yes (Owner) |

### Appointments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/appointments` | Create appointment | Yes |
| `GET` | `/api/v1/appointments` | List appointments | Yes |
| `GET` | `/api/v1/appointments/{id}` | Get appointment details | Yes |
| `PUT` | `/api/v1/appointments/{id}` | Update appointment | Yes |
| `DELETE` | `/api/v1/appointments/{id}` | Cancel appointment | Yes |
| `GET` | `/api/v1/appointments/availability` | Check available slots | Yes |
| `POST` | `/api/v1/appointments/book-from-call` | Book from AI call context | Yes |

### Patients

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/patients` | Create patient record | Yes |
| `GET` | `/api/v1/patients` | List patients | Yes |
| `GET` | `/api/v1/patients/{id}` | Get patient details | Yes |
| `PUT` | `/api/v1/patients/{id}` | Update patient record | Yes |
| `DELETE` | `/api/v1/patients/{id}` | Delete patient | Yes (Owner) |
| `GET` | `/api/v1/patients/search` | Search patients | Yes |

### Calls

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/calls` | List call history | Yes |
| `GET` | `/api/v1/calls/recent` | Get recent calls | Yes |
| `GET` | `/api/v1/calls/stats` | Get call statistics | Yes |
| `GET` | `/api/v1/calls/{id}` | Get call details & transcript | Yes |

### Knowledge Base

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/knowledge-base` | Create KB entry | Yes (Admin) |
| `GET` | `/api/v1/knowledge-base` | List KB entries | Yes |
| `GET` | `/api/v1/knowledge-base/{id}` | Get KB entry | Yes |
| `PUT` | `/api/v1/knowledge-base/{id}` | Update KB entry | Yes (Admin) |
| `DELETE` | `/api/v1/knowledge-base/{id}` | Delete KB entry | Yes (Admin) |
| `POST` | `/api/v1/knowledge-base/seed` | Seed default dental KB | Yes (Admin) |

### Analytics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/analytics/dashboard` | Get dashboard summary | Yes |
| `GET` | `/api/v1/analytics/time-series` | Get time-series data | Yes |
| `GET` | `/api/v1/analytics/top-services` | Get top-requested services | Yes |

### Billing

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/billing/create-checkout-session` | Start Stripe checkout | Yes (Owner) |
| `GET` | `/api/v1/billing/subscription` | Get current subscription | Yes |
| `POST` | `/api/v1/billing/cancel` | Cancel subscription | Yes (Owner) |
| `POST` | `/api/v1/billing/update-plan` | Change subscription tier | Yes (Owner) |

### Webhooks

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/webhooks/voice/incoming` | Twilio incoming call webhook | Twilio Sig |
| `POST` | `/api/v1/webhooks/voice/gather` | Twilio speech input webhook | Twilio Sig |
| `POST` | `/api/v1/webhooks/voice/status` | Twilio call status callback | Twilio Sig |
| `POST` | `/api/v1/webhooks/sms/incoming` | Twilio incoming SMS webhook | Twilio Sig |
| `POST` | `/api/v1/webhooks/stripe` | Stripe event webhook | Stripe Sig |

### Health

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/health` | Application health check | No |
| `GET` | `/health/db` | Database connectivity check | No |
| `GET` | `/health/redis` | Redis connectivity check | No |

---

## Tech Stack

### Backend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Primary language | 3.11+ |
| **FastAPI** | Web framework | 0.115+ |
| **SQLAlchemy** | ORM / database toolkit | 2.0+ |
| **Alembic** | Database migrations | 1.13+ |
| **PostgreSQL** | Primary database | 15+ |
| **Redis** | Caching, rate limiting, sessions | 7+ |
| **Pydantic** | Data validation & settings | 2.0+ |
| **Uvicorn** | ASGI server | 0.30+ |
| **Celery** | Background task queue | 5.4+ |

### AI & Voice

| Technology | Purpose | Version |
|-----------|---------|---------|
| **xAI Grok** | Large language model | Grok-3 |
| **Twilio Voice** | Telephony / voice calls | — |
| **Twilio SMS** | SMS notifications | — |
| **Twilio Gather** | Speech-to-text (real-time) | — |

### Frontend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **React** | UI framework | 18+ |
| **Next.js** | React framework (App Router) | 14+ |
| **TypeScript** | Type-safe JavaScript | 5+ |
| **Tailwind CSS** | Utility-first CSS | 3.4+ |
| **shadcn/ui** | Component library | Latest |
| **Recharts** | Data visualization | 2.12+ |
| **Axios** | HTTP client | 1.7+ |

### Integrations

| Technology | Purpose |
|-----------|---------|
| **Stripe** | Payment processing, subscriptions |
| **Google Calendar API** | Calendar sync |
| **SendGrid** | Transactional email |
| **Sentry** | Error monitoring |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **AWS (EC2, RDS, S3, ALB)** | Cloud hosting |
| **Let's Encrypt** | SSL/TLS certificates |
| **Nginx** | Reverse proxy |
| **GitHub Actions** | CI/CD pipeline |

---

## Deployment

For detailed deployment instructions, see **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)**.

### Quick Deployment Options

| Platform | Difficulty | Monthly Cost | Best For |
|----------|-----------|-------------|----------|
| **Docker Compose** (local) | Easy | Free | Development & testing |
| **Railway.app** | Easy | ~$20–50 | MVP, demos, small scale |
| **Heroku** | Medium | ~$50–100 | Small to medium scale |
| **AWS (EC2 + RDS)** | Hard | ~$100–300 | Production, enterprise |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_appointments.py

# Run with verbose output
pytest -v

# Run HIPAA compliance tests only
pytest tests/test_hipaa_compliance.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and development process.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Business Plan](docs/BUSINESS_PLAN.md) | Investor-ready business plan with market analysis and financials |
| [HIPAA Compliance](docs/HIPAA_COMPLIANCE.md) | Comprehensive HIPAA compliance guide and implementation checklist |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Step-by-step deployment for Docker, AWS, Heroku, and Railway |
| [API Documentation](docs/API_DOCUMENTATION.md) | Full API reference with request/response examples |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Contact

- **Website**: [https://grokdentfl.com](https://grokdentfl.com)
- **Email**: hello@grokdentfl.com
- **Support**: support@grokdentfl.com
- **Twitter/X**: [@Renia AIFL](https://x.com/Renia AIFL)

---

<p align="center">
  Made with 🦷 in Florida<br>
  © 2026 Renia AI. All rights reserved.
</p>
