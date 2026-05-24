/* ============================================
   Renia AI — API Client Module
   ============================================ */

const API = {
  baseUrl: '/api/v1',

  /**
   * Core request method with auth header and error handling
   */
  async request(method, path, body = null, params = null) {
    const url = new URL(this.baseUrl + path, window.location.origin);

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
        localStorage.removeItem('renia_token');
        localStorage.removeItem('renia_user');
        window.location.href = 'index.html';
        throw new Error('Session expired. Please log in again.');
      }

      // Handle other error statuses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `Request failed with status ${response.status}`);
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
    return this.request('PUT', '/clinics/', data);
  },

  async updateHours(data) {
    return this.request('PUT', '/clinics/hours', data);
  },

  async updateServices(data) {
    return this.request('PUT', '/clinics/services', data);
  },

  async updateInsurance(data) {
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
    return this.request('POST', '/appointments/', data);
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
    return this.request('POST', '/knowledge/seed');
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
    return this.request('POST', '/billing/checkout', { plan });
  },

  async getSubscription() {
    return this.request('GET', '/billing/subscription');
  },

  async cancelSubscription() {
    return this.request('POST', '/billing/cancel');
  }
};
