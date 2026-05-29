/* ============================================
   Renia AI — API Client Module
   ============================================ */

const RENIA_DEFAULT_API_BASE = '/api/v1';
const RENIA_WORKER_API_BASE = 'https://renia-ai-backend.medsaidkichene.workers.dev/api/v1';

const trimTrailingSlash = (value) => String(value || '').replace(/\/+$/, '');
const trimApiPath = (path) => {
  if (!path || path === '/') return '';
  return `/${String(path).replace(/^\/+/, '').replace(/\/+$/, '')}`;
};

const getBaseApiUrl = () => {
  const configuredBase = window.RENIA_API_BASE || localStorage.getItem('renia_api_base');
  if (configuredBase) return trimTrailingSlash(configuredBase);

  if (typeof window !== 'undefined' && window.location) {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.') || hostname.startsWith('172.');
    if (isLocal) {
      const port = window.location.port;
      if (port && port !== '8000') {
        return `http://${hostname}:8000${RENIA_DEFAULT_API_BASE}`;
      }
      return RENIA_DEFAULT_API_BASE;
    }

    return RENIA_WORKER_API_BASE;
  }
  return RENIA_DEFAULT_API_BASE;
};

const parseBackendError = async (response) => {
  const errorData = await response.json().catch(async () => {
    const text = await response.text().catch(() => '');
    return text ? { message: text } : {};
  });
  return errorData.detail || errorData.message || errorData.error || `Request failed with status ${response.status}`;
};

const parseAppointmentDateTime = (date, time) => {
  if (!date) return null;
  if (date.includes('T')) return date;
  if (!time && /\d{4}-\d{2}-\d{2}\s+\d/.test(date)) {
    const parts = date.split(/\s+/);
    date = parts.shift();
    time = parts.join(' ');
  }

  const rawTime = String(time || '9:00 AM').trim();
  const match = rawTime.match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$/i);
  if (!match) return `${date}T09:00:00`;

  let hours = Number(match[1]);
  const minutes = Number(match[2] || 0);
  const ampm = (match[3] || '').toUpperCase();
  if (ampm === 'PM' && hours < 12) hours += 12;
  if (ampm === 'AM' && hours === 12) hours = 0;
  return `${date}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00`;
};

const formatUiTime = (value) => {
  if (!value) return '9:00 AM';
  const timePart = String(value).includes('T') ? String(value).split('T')[1] : String(value).split(' ')[1] || value;
  const match = timePart.match(/^(\d{1,2}):(\d{2})/);
  if (!match) return String(value);
  let hours = Number(match[1]);
  const minutes = match[2];
  const suffix = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;
  return `${hours}:${minutes} ${suffix}`;
};

const toTitleCaseStatus = (status) => {
  const normalized = String(status || 'scheduled').replace(/_/g, '-').toLowerCase();
  return normalized.split('-').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('-');
};

const API = {
  baseUrl: getBaseApiUrl(),

  /**
   * Core request method with auth header and error handling
   */
  async request(method, path, body = null, params = null) {
    const normalizedPath = trimApiPath(path);
    const url = new URL(trimTrailingSlash(this.baseUrl) + normalizedPath, window.location.origin);

    // Add query parameters
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          url.searchParams.append(key, value);
        }
      });
    }

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add auth token if available
    const token = localStorage.getItem('renia_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers
    };

    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url.toString(), config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        const currentToken = localStorage.getItem('renia_token');
        if (currentToken && currentToken.startsWith('demo_token_')) {
          throw new Error('Demo token not accepted by backend, using fallback data');
        }
        localStorage.removeItem('renia_token');
        localStorage.removeItem('renia_user');
        window.location.href = 'index.html';
        throw new Error('Session expired. Please log in again.');
      }

      // Handle other error statuses
      if (!response.ok) {
        throw new Error(await parseBackendError(response));
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        console.warn('API not available, using fallback data');
        throw new Error('API not available');
      }
      throw error;
    }
  },

  async requestAny(candidates) {
    let lastError = null;
    for (const candidate of candidates) {
      try {
        return await this.request(candidate.method, candidate.path, candidate.body, candidate.params);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error('All API request candidates failed');
  },

  normalizeAppointment(appt) {
    const dt = appt.appointment_datetime || appt.datetime || '';
    const date = appt.date || (dt ? String(dt).split('T')[0].split(' ')[0] : '');
    const patientName = appt.patient_name || appt.name || [appt.patient?.first_name, appt.patient?.last_name].filter(Boolean).join(' ') || 'Patient';
    const service = appt.service || appt.service_type || 'General Checkup';
    const category = service.toLowerCase().includes('emergency')
      ? 'emergency'
      : (service.toLowerCase().includes('whitening') || service.toLowerCase().includes('implant') || service.toLowerCase().includes('cosmetic') ? 'cosmetic' : 'general');

    return {
      id: appt.id,
      date,
      time: appt.time || formatUiTime(dt),
      name: patientName,
      patient_name: patientName,
      service,
      service_type: service,
      category,
      status: toTitleCaseStatus(appt.status),
      notes: appt.notes || ''
    };
  },

  normalizeCall(call) {
    const patientName = [call.patient?.first_name, call.patient?.last_name].filter(Boolean).join(' ');
    const caller = call.caller_name || call.caller || patientName || call.caller_number || call.caller_phone || 'Unknown caller';
    const created = call.created_at ? new Date(call.created_at) : null;
    const status = toTitleCaseStatus(call.status || 'completed');
    const seconds = Number(call.duration_seconds ?? call.duration ?? 0);
    return {
      id: call.id,
      time: call.time || (created && !Number.isNaN(created.getTime()) ? created.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'Recent'),
      caller,
      caller_name: caller,
      phone: call.phone || call.caller_number || call.caller_phone || '',
      duration: seconds,
      language: (call.language || 'en').toLowerCase().startsWith('es') ? 'Spanish' : 'English',
      status,
      statusClass: status.toLowerCase(),
      service: call.service || call.service_type || 'General inquiry',
      transcriptSummary: call.transcriptSummary || call.summary || call.transcript || 'No summary recorded yet.'
    };
  },

  /* ---- Auth Endpoints ---- */

  async login(email, password) {
    return this.request('POST', '/auth/login', { email, password });
  },

  async signup(data) {
    return this.request('POST', '/auth/signup', data);
  },

  async getMe() {
    return this.request('GET', '/auth/me');
  },

  /* ---- Clinic Endpoints ---- */

  async getClinic() {
    return this.request('GET', '/clinics/');
  },

  async updateClinic(data) {
    // Map clinic_name -> name for backend compatibility
    if (data.clinic_name && !data.name) {
      data = { ...data, name: data.clinic_name };
    }
    if (data.zip && !data.zip_code) {
      data = { ...data, zip_code: data.zip };
    }
    return this.request('PUT', '/clinics/', data);
  },

  async updateHours(data) {
    if (!data.hours) {
      data = { hours: data };
    }
    return this.request('PUT', '/clinics/hours', data);
  },

  async updateServices(data) {
    if (Array.isArray(data)) {
      data = { services: data };
    }
    return this.request('PUT', '/clinics/services', data);
  },

  async updateInsurance(data) {
    if (Array.isArray(data)) {
      data = { insurance_accepted: data, insurance: data };
    } else if (data.insurance && !data.insurance_accepted) {
      data = { ...data, insurance_accepted: data.insurance };
    }
    return this.request('PUT', '/clinics/insurance', data);
  },

  async updateVoiceSettings(data) {
    return this.request('PUT', '/clinics/voice-settings', data);
  },

  /* ---- Appointment Endpoints ---- */

  async getAppointments(params = {}) {
    return this.request('GET', '/appointments/', null, params);
  },

  async getTodayAppointments() {
    return this.request('GET', '/appointments/today');
  },

  async createAppointment(data) {
    // Normalize data for backend compatibility
    const normalized = { ...data };
    if (data.patient_name && !data.patient_id) {
      normalized.patient_name = data.patient_name;
    }
    if (data.service && !data.service_type) {
      normalized.service_type = data.service;
    }
    if (data.date && data.time && !data.appointment_datetime) {
      normalized.appointment_datetime = `${data.date} ${data.time}`;
    }
    if (data.name && !data.patient_name && !data.patient_id) {
      normalized.patient_name = data.name;
    }
    if (data.phone_number && !data.phone) {
      normalized.phone = data.phone_number;
    }
    if (!normalized.appointment_datetime && data.date) {
      normalized.appointment_datetime = parseAppointmentDateTime(data.date, data.time);
    } else if (normalized.appointment_datetime) {
      normalized.appointment_datetime = parseAppointmentDateTime(normalized.appointment_datetime);
    }
    return this.request('POST', '/appointments/', normalized);
  },

  async updateAppointment(id, data) {
    return this.request('PUT', `/appointments/${id}`, data);
  },

  async deleteAppointment(id) {
    return this.request('DELETE', `/appointments/${id}`);
  },

  async getAvailability(date) {
    return this.request('GET', '/appointments/availability', null, { date });
  },

  /* ---- Patient Endpoints ---- */

  async getPatients(page = 1) {
    return this.request('GET', '/patients/', null, { page });
  },

  async getPatient(id) {
    return this.request('GET', `/patients/${id}`);
  },

  async createPatient(data) {
    return this.request('POST', '/patients/', data);
  },

  async updatePatient(id, data) {
    return this.request('PUT', `/patients/${id}`, data);
  },

  async searchPatients(q) {
    return this.request('GET', '/patients/search', null, { q });
  },

  /* ---- Call Endpoints ---- */

  async getCalls(params = {}) {
    return this.request('GET', '/calls/', null, params);
  },

  async getRecentCalls() {
    return this.request('GET', '/calls/recent');
  },

  async getCallStats() {
    return this.request('GET', '/calls/stats');
  },

  async getCall(id) {
    return this.request('GET', `/calls/${id}`);
  },

  /* ---- Knowledge Base Endpoints ---- */

  async getKnowledge() {
    return this.request('GET', '/knowledge/');
  },

  async getKnowledgeByCategory(category) {
    return this.request('GET', '/knowledge/', null, { category });
  },

  async createKnowledge(data) {
    return this.request('POST', '/knowledge/', data);
  },

  async updateKnowledge(id, data) {
    return this.request('PUT', `/knowledge/${id}`, data);
  },

  async deleteKnowledge(id) {
    return this.request('DELETE', `/knowledge/${id}`);
  },

  async seedKnowledge() {
    return this.requestAny([
      { method: 'POST', path: '/knowledge/seed' },
      { method: 'POST', path: '/knowledge/seed-defaults' }
    ]);
  },

  /* ---- Analytics Endpoints ---- */

  async getDashboard() {
    return this.request('GET', '/analytics/dashboard');
  },

  async getCallsOverTime(days = 7) {
    return this.request('GET', '/analytics/calls-over-time', null, { days });
  },

  async getBookingsOverTime(days = 7) {
    return this.request('GET', '/analytics/bookings-over-time', null, { days });
  },

  async getTopServices() {
    return this.request('GET', '/analytics/top-services');
  },

  async getLanguageBreakdown() {
    return this.request('GET', '/analytics/language-breakdown');
  },

  /* ---- Billing Endpoints ---- */

  async createCheckout(plan) {
    const planName = typeof plan === 'string' ? plan : (plan.plan_name || plan.plan);
    const payload = {
      plan: planName,
      plan_name: planName,
      success_url: `${window.location.origin}/billing.html?checkout=success`,
      cancel_url: `${window.location.origin}/billing.html?checkout=cancelled`
    };
    return this.requestAny([
      { method: 'POST', path: '/billing/checkout', body: payload },
      { method: 'POST', path: '/billing/create-checkout', body: payload }
    ]);
  },

  async getSubscription() {
    return this.request('GET', '/billing/subscription');
  },

  async cancelSubscription() {
    return this.request('POST', '/billing/cancel');
  }
};
