# 8-HOUR AUTONOMOUS AI BUILD MANDATE — RENIA AI DENTAL SaaS
## MAXIMUM PRIORITY — PRODUCTION-GRADE — NO HALT — NO GATES

```
CLOUDFLARE_API_TOKEN = <cloudflare-api-token>
GITHUB_TOKEN = <github-personal-access-token>
GITHUB_REPO = https://github.com/cheminisifeddine/grokdent-fl
BRANCH = main
WORKSPACE = /home/ubuntu/grokdent-fl
CLOUDFLARE_WORKER = renia-ai-backend
CLOUDFLARE_D1_DB = grokdent-d1
CLOUDFLARE_R2_BUCKET = grokdent-r2
```

---

## CORE DIRECTIVE
You are an autonomous production AI agent with full root-level workspace authority. Your mission is to independently scan, debug, rewrite, expand, optimize, deploy, and production-harden this entire repository into a fully sellable, market-ready AI Dental Receptionist SaaS platform. You will work continuously for 8 hours without prompt gates, without asking for permission, executing every task in sequence with maximum thoroughness. If you encounter errors, you debug and fix. If you find gaps, you build the missing pieces. If tests fail, you repair until green. Do NOT stop until the entire platform is production-ready, all tests pass, and the system is deployable.

---

## PHASE 0 — ENVIRONMENT BOOTSTRAP & GIT SETUP (30 min)

### 0.1 Git Repository Clone & Setup
```bash
cd /home/ubuntu
git clone https://<username>:<github-token>@github.com/cheminisifeddine/grokdent-fl.git
cd grokdent-fl
git remote set-url origin https://<username>:<github-token>@github.com/cheminisifeddine/grokdent-fl.git
git pull origin main
```
- Verify all branches, recent commits, file structure
- Create a `.opencode/` config directory with agent rules if missing

### 0.2 Python Dependencies
```bash
pip install --break-system-packages -r requirements.txt
```
- If pip fails on individual packages, install them one by one with `pip install --break-system-packages <package>`
- Required: fastapi, uvicorn, sqlalchemy, pydantic-settings, httpx, cryptography, python-jose, passlib[bcrypt], twilio, stripe, sendgrid, google-api-python-client, google-auth-httplib2, email-validator, python-multipart
- Ensure `tzdata` is installed for zoneinfo support

### 0.3 Node.js Verification
```bash
node --version  # must be >= 18
cd cloudflare-backend && npm install
```
- Verify all JS files pass `node --check`

### 0.4 Cloudflare Wrangler Setup
```bash
npx wrangler login --api-key $CLOUDFLARE_API_TOKEN
npx wrangler d1 create grokdent-d1 --experimental-backend 2>/dev/null || true
npx wrangler d1 execute grokdent-d1 --file=./schema.sql --local 2>/dev/null || true
```
- Configure wrangler.toml with correct D1 database ID, R2 bucket name, Durable Object bindings
- Set secrets: JWT_SECRET, ENCRYPTION_KEY, XAI_API_KEY, TWILIO_AUTH_TOKEN, STRIPE_SECRET_KEY
- Deploy worker to Cloudflare edge

---

## PHASE 1 — COMPLETE CODEBASE AUDIT & DEEP REFACTORING (90 min)

### 1.1 Full File System Mapping
Walk EVERY directory and file:
```
/home/ubuntu/grokdent-fl/
├── backend/           # FastAPI Python backend
│   ├── api/           # REST API routers (auth, clinics, appointments, patients, calls, knowledge, billing, webhooks, analytics)
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic layer
│   ├── voice/         # Telephony/voice AI pipeline
│   ├── middleware/     # HIPAA audit, security middleware
│   └── utils/         # Timezone, Florida data helpers
├── cloudflare-backend/ # Cloudflare Workers + Durable Objects
│   └── src/           # Hono-based serverless API, DO classes
├── frontend/          # Static HTML/JS frontend SPA
│   ├── js/            # Client-side JavaScript modules
│   └── assets/        # Images, static assets
├── scripts/           # Deployment, seeding, testing
└── docs/              # Documentation
```

### 1.2 Synchronous Block Detection & Remediation
- Scan EVERY Python file for blocking IO in async functions
- Convert ALL `httpx.get/post` calls in async contexts to `httpx.AsyncClient`
- Move ALL Google Calendar API calls into `ThreadPoolExecutor` via `asyncio.run_in_executor()`
- Move ALL SQLAlchemy `Base.metadata.create_all()` and heavy sync ops into thread pools
- Replace ALL `time.sleep()` calls with `asyncio.sleep()`
- Check for ANY `requests.get/requests.post` usage — replace with `httpx`
- Verify NO synchronous database calls inside FastAPI async route handlers

### 1.3 Exception Handling Audit
- Find EVERY `await` call that is NOT wrapped in `try/except`
- Add try/except blocks around ALL external API calls (xAI, Twilio, Stripe, Cal.com, Calendly, Google, SendGrid)
- Add try/except blocks around ALL database operations in routes
- Add try/except blocks around ALL WebSocket operations
- Add try/except blocks inside EVERY `conversation_manager.py` Grok API call
- Add try/except blocks inside EVERY `voice_handler.py` speech processing call
- Never use bare `except:` — always catch specific exceptions or at minimum `except Exception as e`
- ALL catch blocks must log the error with logger.error() — NO silent exception swallowing

### 1.4 Data Schema Standardization
Verify consistency across ALL layers for the Patient Intake schema:
- **Model** (`backend/models/patient.py`, `backend/models/patient_intake.py`): Name, Phone, ReasonForCall, AppointmentDate
- **Schema** (`backend/schemas/patient_intake.py`): PatientIntakeCreate, PatientIntakeResponse
- **API Route** (`backend/api/patients.py`): Create/Read/Update endpoints
- **Encryption**: ALL PHI fields encrypted via `encryption_service.py` (Fernet) or `hipaa_crypto.py` (AES-256-GCM)
- **Frontend**: API client calls match backend field names exactly
- Fix ALL field name mismatches: `clinic_name` vs `name`, `patient_name` vs `patient_id`, `service` vs `service_type`

### 1.5 Security Hardening
- Remove ALL hardcoded API keys, tokens, and secrets — search with `rg "xai-" /home/ubuntu/grokdent-fl/` and similar
- Verify NO keys appear in: frontend JS, HTML attributes, inline scripts, HTML comments
- Twilio webhooks: Add HMAC-SHA256 signature verification in `backend/api/webhooks.py`
- Stripe webhooks: Verify signature verification is present
- JWT: Ensure SECRET_KEY is loaded from env, never hardcoded
- Encryption: ENCRYPTION_KEY must be required — no fallback, no generate-on-the-fly
- CORS: Limit origins in `backend/main.py` — NOT wildcard `*` in production
- Passwords: Cloudflare backend must use PBKDF2 (600K iterations) NOT SHA-256
- Rate limiting: Add rate limiter to auth endpoints (/signup, /login)
- Input validation: ALL Pydantic models must have proper constraints (min_length, max_length, regex patterns)
- Content Security Policy: Add CSP meta tag to ALL HTML pages
- SQL injection: Verify ALL database queries use parameterized queries — NO string interpolation

### 1.6 Import & Module Validation
- Verify ALL Python files compile: `python -m py_compile <file>` for every .py
- Verify ALL imports resolve: import every module in the chain
- Fix ALL missing imports: `Optional`, `Dict`, `List`, `Any`, `datetime`
- Verify ALL `__init__.py` files re-export necessary symbols
- Verify NO circular imports exist
- Verify ALL JavaScript files pass: `node --check <file>` for every .js

---

## PHASE 2 — TELEPHONY & STREAMING CORE PIPELINE (90 min)

### 2.1 WebSocket Architecture Hardening
**Python Backend (`backend/main.py`):**
- Ensure `DashboardConnectionManager` handles 1000+ concurrent WebSocket connections
- Add heartbeat ping/pong with configurable interval (30s default)
- Add stale connection pruning — remove dead sockets after 120s silence
- Add broadcast with `return_exceptions=True` so one dead socket doesn't crash the broadcast
- Add connection metrics: track active connections per clinic_id, total connections
- Add graceful shutdown: close all connections on app shutdown event

**Cloudflare Backend (`cloudflare-backend/src/durable-objects.js`):**
- Complete the `RealtimeDashboardDO` class with full lifecycle management
- Add per-clinic session tracking
- Add heartbeat alarm that pings all clients every 30 seconds
- Add stale session cleanup (remove after 5 minutes of silence)
- Add message queue for offline delivery
- Add proper error handling for closed/malformed sessions
- Add rate limiting per client (max 10 messages/second)
- Wire the WebSocket upgrade route in `index.js` to proxy requests to the DO

### 2.2 Audio Streaming Pipeline
**Frontend Voice Agent (`frontend/js/voice-agent.js`):**
- Ensure PCM audio chunks are coalesced into playback buffers of at least 1024 samples
- Add debounce mechanism: wait 50ms after last chunk before flushing to playback
- Add adaptive buffer sizing: detect network jitter, adjust buffer coalesce delay
- Add audio quality monitoring: track chunks dropped, chunks played, latency
- Add graceful fallback: if AudioContext is unavailable, show visible error
- Add reconnection logic: if xAI WebSocket drops, auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, 16s, max 5 attempts)
- Add connection health monitoring: track last message timestamp, detect silent disconnects

**Backend Proxy (`cloudflare-backend/src/index.js`):**
- Session token endpoint MUST be authenticated
- Session token endpoint MUST cache tokens (reuse until 30s before expiry)
- TTS endpoint MUST be authenticated
- TTS endpoint MUST validate input text length (< 4096 chars)
- Simulate endpoint MUST be authenticated
- Simulate endpoint MUST validate scenario and voice parameters
- ALL voice endpoints MUST rate-limit (max 30 req/min per IP)

### 2.3 Conversational Interrupt Handling
- When `input_audio_buffer.speech_started` event fires:
  - Immediately flush ALL queued audio playback
  - Suspend AudioContext
  - Send `response.cancel` to xAI WebSocket
  - Clear any pending TTS response
  - Resume AudioContext for microphone input
- When `input_audio_buffer.speech_stopped` event fires:
  - Resume AudioContext for playback
  - Allow next response to begin
- Implement dead-man switch: if no speech detected for 60 seconds, end call gracefully

### 2.4 Twilio Integration Completeness
- Verify ALL TwiML responses are valid XML
- Add proper SSML support for Google/Amazon Polly voices on Twilio
- Add `<Record>` support for voicemail fallback
- Add `<Dial>` support for warm transfer to human
- Add `<Queue>` support for call queuing during high volume
- Verify status callback webhooks are processed correctly
- Add call recording storage to R2 bucket
- Add transcript storage to D1 database with encryption

---

## PHASE 3 — SCHEDULING & OUTBOUND SYNC ENGINE (90 min)

### 3.1 Cal.com Integration
**File: `backend/services/scheduling_service.py`**
- Complete the `get_calcom_slots()` method with full error handling
- Complete the `create_calcom_booking()` method with patient data mapping
- Add `cancel_calcom_booking()` method for appointment cancellation sync
- Add `get_calcom_booking()` method to verify booking status
- Add retry logic: 3 retries with exponential backoff (1s, 2s, 4s)
- Add webhook verification for Cal.com booking confirmations
- Set `timeZone: "US/Eastern"` explicitly on all Cal.com payloads
- Validate Cal.com API key and event type ID at service init

### 3.2 Calendly Integration
**File: `backend/services/scheduling_service.py`**
- Complete the `get_calendly_conflicts()` method for full double-booking protection
- Complete the `create_calendly_booking()` with proper API calls
- Add `cancel_calendly_booking()` method
- Fetch and cache the Calendly user URI on service init
- Add proper OAuth PAT validation
- Verify all Calendly API calls use `Authorization: Bearer <PAT>` header

### 3.3 Google Calendar Integration
**File: `backend/services/calendar_service.py`**
- Verify service account credentials parsing from JSON env var
- Add calendar list endpoint to discover available calendars
- Add event update method (not just create/delete)
- Add recurrence rule support for recurring appointments
- Add reminders configuration (SMS + email at 24h and 1h before appointment)
- Add color coding by service type
- Add attendee management (add doctor/staff to event)

### 3.4 Double-Booking Protection
- Implement strict lock-based booking: acquire advisory lock before checking availability
- Cross-reference ALL sources: local DB + Google Calendar + Cal.com + Calendly
- Return detailed conflict information when booking is blocked
- Add 5-minute buffer between appointments (configurable per clinic)
- Add same-day booking cutoff (default: no online booking within 2 hours)
- Add maximum concurrent appointments per provider
- Implement atomic transaction: all external bookings must succeed OR all must rollback

### 3.5 Florida Timezone Enforcement
**File: `backend/utils/timezone.py`**
- ALL datetime operations must use `ZoneInfo("US/Eastern")` — NO pytz
- ALL naive datetimes must be assumed as Eastern Time (Florida clinics)
- ALL API responses must include timezone offset information
- ALL scheduling logic must convert to Eastern before checking availability
- Handle DST transitions correctly (spring forward, fall back)
- Validate that ALL clinic hours are stored in Eastern Time
- Add timezone display helper with cross-platform formatting

### 3.6 HIPAA Data Isolation
**File: `backend/services/hipaa_data_layer.py`**
- Complete the `encrypt_patient_data()` with field-level encryption for ALL PHI fields
- Complete the `decrypt_patient_data()` with proper error handling
- Complete the `encrypt_intake_profile()` with AES-256-GCM + associated data
- Complete the `decrypt_intake_profile()` with auth tag verification
- Complete the `encrypt_call_transcript()` / `decrypt_call_transcript()` methods
- Add key rotation support (re-encrypt all data with new key)
- Add audit logging for ALL encryption/decryption operations
- Add encrypted at-rest verification: periodically scan DB for unencrypted PHI

---

## PHASE 4 — FRONT OFFICE DASHBOARD & ANALYTICS (90 min)

### 4.1 Real-Time Dashboard
**File: `frontend/dashboard.html`**
- Complete the metric cards with live-animated counters
- Complete the recent calls feed with expandable transcripts
- Complete the today's appointments list with status badges
- Complete the charts: calls-over-time, services breakdown, language distribution
- Add clinic-specific metric: revenue captured, calls answered, appointments booked
- Add live updating via WebSocket connection

**File: `frontend/js/dashboard.js`**
- Complete `loadDashboard()` with full API integration
- Complete `renderMetricCards()` with proper formatting
- Complete `renderRecentCalls()` with call details
- Complete `renderTodayAppointments()` with appointment actions
- Complete `initCharts()` with Chart.js initialization
- Complete `setupWebSocket()` with proper event routing
- Add `loadRecentCalls()` and `loadTodayAppointments()` with error handling

### 4.2 Analytics Module
**File: `backend/api/analytics.py`**
- Complete ALL analytics endpoints with real database queries
- Dashboard: call count today, bookings today, revenue estimate, satisfaction score
- Calls Over Time: last 7/30/90 days with proper date bucketing
- Bookings Over Time: new vs. returning patient breakdown
- Top Services: count by service type with percentages
- Language Breakdown: English vs. Spanish percentages
- Revenue Attribution: revenue captured vs. missed

**File: `frontend/analytics.html`**
- Complete charts: line chart (calls), line chart (bookings), doughnut (languages), horizontal bar (services)
- Add date range selector (7d, 30d, 90d, custom)
- Add metric summary cards at top
- Add export to CSV functionality

### 4.3 Appointment Management
**File: `frontend/appointments.html`**
- Complete calendar view (day, week, month)
- Add appointment creation modal with patient search
- Add appointment editing with drag-to-reschedule
- Add conflict detection visualization
- Add patient communication log

### 4.4 Patient Management
**File: `frontend/js/api.js`**
- Complete ALL API methods with proper parameter mapping
- Ensure `createAppointment()` maps {patient_name, service, date, time} -> {patient_id, appointment_datetime, service_type}
- Ensure `updateClinic()` maps {clinic_name} -> {name}
- Add `searchPatients()` with proper query parameter handling
- Add proper error handling: 401 redirect, 500 toast, network error fallback

### 4.5 Settings & Configuration
**File: `frontend/settings.html`**
- Complete clinic profile form (name, phone, address, hours)
- Complete voice settings (voice selection, welcome message, Spanish toggle)
- Complete services list (add/remove services with pricing)
- Complete insurance list (accepted providers)
- Complete emergency settings (on-call contact, triage rules)

---

## PHASE 5 — LANDING PAGE & CONVERSION OPTIMIZATION (60 min)

### 5.1 Landing Page Excellence
**File: `frontend/index.html`**
- Hero: "Your front desk. Infinitely scalable." — punchy, clear value prop
- Trust strip: Real Florida clinic names in marquee
- Stats band: $2.4M+, 14,200+ calls, 98.7% satisfaction
- Feature grid: 6 cards with hover-to-dark transitions, each showing a core capability
- Live simulator: Interactive voice agent demo with Carlos/Emily/James scenarios
- ROI calculator: Slider-based revenue calculator with dark theme
- Pricing: 3-tier ($299/$599/$999) with clear differentiation
- Final CTA: Dark section with compelling call to action
- Every section must have proper spacing, typography, and responsive design
- ALL links must work: signup, login, watch demo, pricing anchors

### 5.2 Conversion Copywriting
- Headline: Quantify the problem ("every missed call is lost revenue")
- Sub-headline: Position as the solution ("Florida's first AI-native dental operator")
- Social proof: "40+ Florida clinics", "12x average ROI", "9-day payback"
- Risk reversal: "Free 7-day trial", "Cancel anytime", "HIPAA BAA signed instantly"
- Scarcity/urgency: "Your first patient is calling right now"
- Each feature: Benefits-focused ("24/7 Call Capture"), not technical ("WebSocket integration")

### 5.3 Multi-Tenant Signup Flow
**File: `frontend/signup.html`**
- Step 1: Clinic name, admin email, password
- Step 2: Clinic phone number, address, hours
- Step 3: Services offered, insurance accepted
- Step 4: Voice preferences, welcome message
- On completion: Create clinic + admin user, issue JWT, redirect to dashboard
- ALL form fields must have validation (required, min length, email format)
- API calls must handle errors gracefully with visible error messages

---

## PHASE 6 — BILLING & SUBSCRIPTION ENGINE (60 min)

### 6.1 Stripe Integration
**File: `backend/api/billing.py`**
- Complete `create_checkout_session()` with real Stripe price IDs from env
- Complete `stripe_webhook()` with full event handling:
  - `checkout.session.completed` -> activate subscription
  - `invoice.payment_succeeded` -> update subscription status
  - `invoice.payment_failed` -> notify clinic, pause service
  - `customer.subscription.deleted` -> deactivate, send exit survey
- Add `get_subscription_status()` with accurate plan details
- Add `cancel_subscription()` with feedback collection
- Add subscription upgrade/downgrade with proration
- Store Stripe customer ID in clinic record
- Store Stripe subscription ID in clinic record
- Add invoice history endpoint

### 6.2 Usage Tracking
- Track call count per clinic per month against plan limits
- Send warning at 80%, block at 100% with upgrade prompt
- Track API token usage for voice agent operations
- Add usage dashboard in billing page

### 6.3 Billing Page
**File: `frontend/billing.html`**
- Current plan display with feature list
- Plan comparison table
- Upgrade/downgrade buttons
- Invoice history
- Payment method management
- Cancel subscription flow

---

## PHASE 7 — TESTING & QUALITY ASSURANCE (60 min)

### 7.1 Syntax & Compilation Tests
Run and fix until 100% clean:
```bash
# Python: all files must compile
for f in $(find /home/ubuntu/grokdent-fl -name "*.py" ! -path "*/.venv/*" ! -path "*/__pycache__/*"); do
  python -m py_compile "$f" || echo "FAIL: $f"
done

# JavaScript: all files must pass
for f in $(find /home/ubuntu/grokdent-fl/{frontend,cloudflare-backend} -name "*.js"); do
  node --check "$f" || echo "FAIL: $f"
done
```

### 7.2 Import & Module Resolution Tests
```bash
cd /home/ubuntu/grokdent-fl && python -c "
from backend.config import settings
from backend.database import Base, SessionLocal
from backend.main import app
from backend.services.encryption_service import encryption_service
from backend.services.hipaa_crypto import hipaa_crypto
from backend.services.hipaa_data_layer import hipaa_data_layer
from backend.services.scheduling_service import scheduling_service
from backend.services.calendar_service import calendar_service
from backend.services.notification_service import notification_service
from backend.services.emergency_service import emergency_service
from backend.services.insurance_service import InsuranceService
from backend.services.pms_service import MockPMSService
from backend.services.analytics_service import AnalyticsService
from backend.voice.grok_client import GrokVoiceClient
from backend.voice.conversation_manager import ConversationManager, ConversationState
from backend.voice.voice_handler import VoiceHandler
from backend.voice.language_router import LanguageRouter
from backend.voice.dental_prompts import build_system_prompt, build_spanish_prompt
from backend.schemas.patient_intake import PatientIntakeCreate, PatientIntakeResponse
print('ALL IMPORTS PASSED')
"
```

### 7.3 FastAPI Application Instantiation
```bash
cd /home/ubuntu/grokdent-fl && python -c "
from backend.main import app
print(f'App: {app.title} v{app.version}')
print(f'Routes: {len(app.routes)}')
for route in app.routes:
    if hasattr(route, 'path'):
        print(f'  {route.methods if hasattr(route, \"methods\") else \"\"} {route.path}')
"
```

### 7.4 Route Coverage & Integrity
- Verify ALL API routes exist: auth, clinics, appointments, patients, calls, knowledge, billing, webhooks, analytics
- Verify ALL Cloudflare Worker routes match the Python backend routes
- Verify frontend API client calls match actual backend endpoints
- Verify WebSocket upgrade route is registered
- Verify health check endpoint returns 200
- Verify static file serving works for frontend assets

### 7.5 Frontend Integration Tests
- All HTML pages load without JavaScript errors
- All forms submit data correctly
- All buttons trigger intended actions
- Navigation links resolve correctly
- Responsive design works on mobile/tablet/desktop viewports
- CSS classes render correctly in Chromium/Firefox/Safari

### 7.6 Fix Recursively
If ANY test fails:
1. Capture the exact error message and stack trace
2. Locate the root cause (file, line number)
3. Fix the root cause (not the symptom)
4. Re-run the test
5. Continue until 100% pass rate
6. Do not skip or comment out failing tests

---

## PHASE 8 — DEPLOYMENT & PRODUCTION HARDENING (60 min)

### 8.1 Cloudflare Worker Deployment
```bash
cd /home/ubuntu/grokdent-fl/cloudflare-backend

# Set secrets
npx wrangler secret put JWT_SECRET
npx wrangler secret put ENCRYPTION_KEY
npx wrangler secret put XAI_API_KEY
npx wrangler secret put TWILIO_AUTH_TOKEN
npx wrangler secret put STRIPE_SECRET_KEY

# Create D1 database if not exists
npx wrangler d1 create grokdent-d1

# Apply schema
npx wrangler d1 execute grokdent-d1 --file=./schema.sql

# Deploy Worker
npx wrangler deploy

# Verify deployment
npx wrangler tail
```

### 8.2 Environment Variables Checklist
Create a `.env.example` with ALL required variables:
```
XAI_API_KEY=          # xAI / Grok API token
TWILIO_ACCOUNT_SID=   # Twilio primary account identifier
TWILIO_AUTH_TOKEN=    # Twilio secret auth credential
TWILIO_PHONE_NUMBER=  # Provisioned Twilio phone number
STRIPE_SECRET_KEY=    # Stripe secret API key
STRIPE_WEBHOOK_SECRET= # Stripe webhook signing secret
ENCRYPTION_KEY=       # Fernet/AES-256 symmetric encryption key (32-char base64)
JWT_SECRET=           # HMAC signing secret for JSON Web Tokens
SECRET_KEY=           # FastAPI secret key for session signing
DATABASE_URL=         # SQLAlchemy database connection string (postgresql:// or sqlite:///)
SENDGRID_API_KEY=     # SendGrid API key for email/SMS notifications
GOOGLE_CALENDAR_CREDENTIALS_JSON= # Google service account JSON credentials
CALCOM_API_KEY=       # Cal.com API key
CALCOM_EVENT_TYPE_ID= # Cal.com event type ID for appointment slots
CALCOM_API_URL=       # Cal.com API base URL (typically https://api.cal.com/v1)
CALENDLY_PAT=         # Calendly Personal Access Token
CALENDLY_EVENT_TYPE_URI= # Calendly event type URI
CALENDLY_API_URL=     # Calendly API base URL
DEBUG=                # Boolean: enable debug mode
ENVIRONMENT=          # development | staging | production
ACCESS_TOKEN_EXPIRE_MINUTES=60  # JWT token lifetime
XAI_BASE_URL=https://api.x.ai/v1
STRIPE_PRICE_STARTER=price_starter_mock_123
STRIPE_PRICE_PROFESSIONAL=price_professional_mock_456
STRIPE_PRICE_ENTERPRISE=price_enterprise_mock_789
```

### 8.3 Production Configuration
- CORS: Restrict to actual frontend domain, NOT wildcard
- Database: Force PostgreSQL in production, warn on SQLite
- Logging: Set level to WARNING in production, INFO in development
- Debug: Disable in production (settings.DEBUG = False)
- SSL/TLS: Enforce HTTPS redirection
- Headers: Add security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- Rate Limiting: Add to ALL API endpoints (100 req/min for standard, 5 req/min for auth)
- WebSocket: Add connection limit (max 100 per clinic_id)

### 8.4 Database Migrations
- Verify ALL SQLAlchemy models have corresponding D1 schema entries
- Verify ALL column types match between Python models and SQL schema
- Verify ALL foreign key relationships are properly defined
- Verify ALL indexes are created for frequently queried columns
- Verify encryption columns have sufficient length for AES-256-GCM ciphertexts

### 8.5 Monitoring & Alerting Setup
- Add health check endpoint: `/health` returns 200 with version
- Add metrics endpoint: `/api/v1/system/metrics` returns connection counts, error rates
- Add Cloudflare Worker analytics dashboard
- Set up D1 database monitoring (query latency, storage usage)
- Set up R2 bucket monitoring (storage usage, request count)
- Add Sentry or similar error tracking integration
- Add uptime monitoring (ping health check every 60 seconds)

---

## PHASE 9 — DOCUMENTATION & HANDOVER (30 min)

### 9.1 API Documentation
- Update `docs/API_DOCUMENTATION.md` with ALL endpoints, request/response schemas
- Include authentication method (Bearer JWT)
- Include rate limits
- Include example requests and responses
- Auto-generate OpenAPI spec and verify it's accessible at `/api/docs`

### 9.2 Deployment Guide
- Update `docs/DEPLOYMENT_GUIDE.md` with step-by-step instructions
- Include prerequisites (Node.js 18+, Python 3.11+, Cloudflare account)
- Include environment variable setup
- Include database provisioning
- Include worker deployment
- Include verification steps

### 9.3 Business Plan
- Update `docs/BUSINESS_PLAN.md` with current metrics and features
- Include pricing model analysis
- Include market opportunity sizing
- Include competitive landscape
- Include growth projections

### 9.4 HIPAA Compliance
- Update `docs/HIPAA_COMPLIANCE.md` with implementation details
- Document encryption methods (Fernet AES-128, AES-256-GCM)
- Document audit logging
- Document access controls
- Document data retention and deletion policies
- List all PHI fields and their encryption status

---

## CONTINUOUS EXECUTION LOOP

Throughout the 8 hours, run this loop continuously:

```
while TASK_REMAINING:
    step = get_next_step()
    execute(step)
    if step.failed():
        error = capture_stack_trace()
        root_cause = locate_root_cause(error)
        fix(root_cause)
        re_execute(step)
    verify(step)
    mark_complete(step)
    commit_if_major_milestone()
```

### Git Commit Strategy
Commit after each major milestone with descriptive messages:
- `fix: resolve async blocking in appointment router`
- `feat: complete Cal.com booking integration with double-booking protection`
- `fix: remove hardcoded API keys from frontend, add env-based injection`
- `feat: add WebSocket Durable Object with heartbeat and reconnection`
- `fix: migrate all pytz usage to zoneinfo for cross-platform compatibility`
- `feat: add PBKDF2 password hashing to Cloudflare Worker backend`
- `feat: complete HIPAA data isolation layer with AES-256-GCM`
- `feat: add rate limiting to auth endpoints`
- `fix: resolve all field name mismatches between frontend and backend`
- `refactor: redesign landing page for enterprise conversion optimization`
- `test: all 46 Python modules import successfully, 12 JS files syntax-valid`
- `deploy: Cloudflare Worker deployed to edge with all secrets configured`

Push to GitHub after EVERY commit:
```bash
git add -A && git commit -m "<message>" && git push origin main
```

---

## SUCCESS CRITERIA — DO NOT EXIT UNTIL:

- [ ] ALL 46+ Python files compile without syntax errors
- [ ] ALL 12+ JavaScript files pass `node --check`
- [ ] ALL imports resolve at the module level
- [ ] FastAPI app instantiates without errors
- [ ] ALL 53 routes are registered and reachable
- [ ] ZERO hardcoded secrets, API keys, or tokens in the codebase
- [ ] ALL API calls have try/except blocks with logging
- [ ] ALL sync blocking calls moved to thread pools in async contexts
- [ ] Scheduling engine integrates with Cal.com, Calendly, and Google Calendar
- [ ] Double-booking protection works across all scheduling platforms
- [ ] HIPAA encryption layer wraps all PHI fields
- [ ] WebSocket pipeline supports real-time streaming with heartbeat
- [ ] Cloudflare Worker deployed to production edge
- [ ] Landing page is production-quality with working simulator
- [ ] All documentation is updated and complete
- [ ] Git history is clean with descriptive commit messages
- [ ] `git push origin main` succeeds with no rejections
- [ ] Cloudflare Worker responds to health check with 200

---

## CRITICAL RULES

1. NEVER delete files without understanding their purpose
2. NEVER change the database schema without updating both SQLAlchemy models AND D1 SQL
3. NEVER commit API keys, tokens, or secrets — use environment variables ONLY
4. NEVER leave empty catch blocks — at minimum log the error
5. NEVER use `requests` library inside async functions — use `httpx.AsyncClient`
6. NEVER use `time.sleep()` in async functions — use `asyncio.sleep()`
7. NEVER assume a library is available — verify with pip list first
8. NEVER skip a test — if it fails, fix the root cause
9. ALWAYS use the existing code conventions — match formatting, naming, patterns
10. ALWAYS push to GitHub after completing a major phase
11. ALWAYS verify before committing — run syntax checks, import tests
12. ALWAYS log errors with context (function name, parameters, stack trace)

---

## INFERENCE MODE
Execute using internal chain-of-thought reasoning. Work quietly. Minimize text output to preserve context. Maximum concurrency — run parallel tasks when safe. No pause between phases — continuous autonomous execution.

**START TIME: NOW | DURATION: 8 HOURS | MODE: FULL AUTONOMOUS | SCOPE: COMPLETE SAAS PRODUCTION BUILD**
