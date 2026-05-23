-- GrokDent FL — Cloudflare D1 SQL Schema

-- 1. Clinics table
CREATE TABLE IF NOT EXISTS clinics (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  phone TEXT,
  email TEXT,
  address TEXT,
  city TEXT,
  state TEXT DEFAULT 'FL',
  zip_code TEXT,
  timezone TEXT DEFAULT 'US/Eastern',
  services TEXT, -- JSON string array
  hours TEXT, -- JSON string dict
  insurance_accepted TEXT, -- JSON string array
  emergency_contact_name TEXT,
  emergency_contact_phone TEXT,
  grok_voice_id TEXT DEFAULT 'Ash',
  twilio_phone_number TEXT,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  subscription_plan TEXT DEFAULT 'starter',
  subscription_status TEXT DEFAULT 'trial',
  policies TEXT,
  welcome_message TEXT,
  spanish_enabled INTEGER DEFAULT 1, -- 0 = False, 1 = True
  is_active INTEGER DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users table (Practice admin/staff)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT DEFAULT 'staff', -- admin | staff
  is_active INTEGER DEFAULT 1,
  last_login DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(clinic_id) REFERENCES clinics(id) ON DELETE CASCADE
);

-- 3. Patients table (AES Encrypted PII fields)
CREATE TABLE IF NOT EXISTS patients (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  phone_encrypted TEXT,
  email_encrypted TEXT,
  dob_encrypted TEXT,
  insurance_provider TEXT,
  insurance_id_encrypted TEXT,
  preferred_language TEXT DEFAULT 'en', -- en | es
  notes_encrypted TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(clinic_id) REFERENCES clinics(id) ON DELETE CASCADE
);

-- 4. Appointments table
CREATE TABLE IF NOT EXISTS appointments (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  patient_id TEXT,
  appointment_datetime TEXT NOT NULL, -- YYYY-MM-DD HH:MM:SS
  duration_minutes INTEGER DEFAULT 30,
  service_type TEXT,
  status TEXT DEFAULT 'scheduled', -- scheduled | confirmed | cancelled | completed
  notes TEXT,
  google_calendar_event_id TEXT,
  created_via TEXT DEFAULT 'web_dashboard', -- ai_voice | web_dashboard | manual
  reminder_sent INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(clinic_id) REFERENCES clinics(id) ON DELETE CASCADE,
  FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE SET NULL
);

-- 5. Call Logs table
CREATE TABLE IF NOT EXISTS call_logs (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  patient_id TEXT,
  twilio_call_sid TEXT UNIQUE NOT NULL,
  direction TEXT DEFAULT 'inbound', -- inbound | outbound
  caller_number TEXT,
  called_number TEXT,
  duration_seconds INTEGER DEFAULT 0,
  status TEXT DEFAULT 'completed', -- completed | missed | busy | voicemail
  transcript_encrypted TEXT,
  summary TEXT,
  sentiment TEXT DEFAULT 'neutral', -- positive | neutral | negative
  language TEXT DEFAULT 'en', -- en | es
  actions_taken TEXT, -- JSON string array
  recording_url_encrypted TEXT,
  is_emergency INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(clinic_id) REFERENCES clinics(id) ON DELETE CASCADE,
  FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE SET NULL
);

-- 6. Knowledge Base table (FAQs)
CREATE TABLE IF NOT EXISTS knowledge_base (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  category TEXT NOT NULL, -- hours | location | services | insurance | pricing | policies | emergency | general
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  answer_spanish TEXT,
  is_active INTEGER DEFAULT 1,
  priority INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(clinic_id) REFERENCES clinics(id) ON DELETE CASCADE
);

-- 7. Insurance Providers table
CREATE TABLE IF NOT EXISTS insurance_providers (
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL, -- PPO | HMO | DHMO | Medicaid | Medicare
  florida_specific INTEGER DEFAULT 0,
  phone TEXT,
  website TEXT,
  is_active INTEGER DEFAULT 1
);

-- 8. Audit Logs table (HIPAA compliance logs)
CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  clinic_id TEXT NOT NULL,
  user_id TEXT,
  action TEXT NOT NULL, -- view | create | update | delete | access | export
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  ip_address TEXT,
  user_agent TEXT,
  details TEXT, -- JSON string dict
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
