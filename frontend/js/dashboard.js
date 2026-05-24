/* ============================================
   Renia AI — Dashboard Page Logic
   ============================================ */

const Dashboard = {
  charts: {},

  /**
   * Load all dashboard data
   */
  async loadDashboard() {
    // Populate sidebar user
    Auth.populateSidebarUser();

    // Try to load from API, fallback to sample data
    try {
      const [dashboard, recentCalls, todayAppts] = await Promise.all([
        API.getDashboard(),
        API.getRecentCalls(),
        API.getTodayAppointments()
      ]);

      this.renderMetricCards(dashboard);
      this.renderRecentCalls(recentCalls);
      this.renderTodayAppointments(todayAppts);
    } catch (error) {
      console.warn('Using sample dashboard data:', error.message);
      this.renderMetricCards(this.getSampleMetrics());
      this.renderRecentCalls(this.getSampleCalls());
      this.renderTodayAppointments(this.getSampleAppointments());
    }

    // Initialize charts
    this.initCharts();

    // Setup WebSocket
    this.setupWebSocket();
  },

  /**
   * Render metric cards with animated counters
   */
  renderMetricCards(metrics) {
    const data = metrics || this.getSampleMetrics();

    const cards = [
      { id: 'metric-calls', value: data.calls_today || 47, trend: data.calls_trend || '+12%', trendDir: 'up' },
      { id: 'metric-booked', value: data.booked_today || 12, trend: data.booked_trend || '+8%', trendDir: 'up' },
      { id: 'metric-revenue', value: data.revenue_today || 3240, trend: data.revenue_trend || '+15%', trendDir: 'up' },
      { id: 'metric-satisfaction', value: data.satisfaction || 96, trend: data.satisfaction_trend || '+2%', trendDir: 'up' }
    ];

    cards.forEach(card => {
      const el = document.getElementById(card.id);
      if (!el) return;

      const valueEl = el.querySelector('.value');
      const trendEl = el.querySelector('.trend');

      if (valueEl) {
        const format = valueEl.getAttribute('data-format');
        animateCounter(valueEl, card.value, 1200);
      }

      if (trendEl) {
        trendEl.textContent = card.trend;
        trendEl.className = `trend ${card.trendDir}`;
        trendEl.textContent = (card.trendDir === 'up' ? '↑ ' : '↓ ') + card.trend;
      }
    });
  },

  /**
   * Render recent calls feed
   */
  renderRecentCalls(calls) {
    const container = document.getElementById('recent-calls-list');
    if (!container) return;

    const data = calls || this.getSampleCalls();

    container.innerHTML = data.map(call => `
      <div class="call-item" data-id="${call.id || ''}">
        <div class="call-item-avatar">${call.sentiment_emoji || '📞'}</div>
        <div class="call-item-info">
          <div class="call-item-name">${escapeHtml(call.caller_name || call.caller_phone || 'Unknown')}</div>
          <div class="call-item-meta">${call.time || getRelativeTime(call.created_at)} · ${call.language === 'es' ? '🇪🇸 Spanish' : '🇺🇸 English'}</div>
        </div>
        <div class="call-item-right">
          <div class="call-item-duration">${formatDuration(call.duration || 0)}</div>
          <span class="badge badge-${call.status === 'completed' ? 'success' : call.status === 'missed' ? 'danger' : 'warning'}">${call.status || 'completed'}</span>
        </div>
      </div>
    `).join('');
  },

  /**
   * Render today's appointments list
   */
  renderTodayAppointments(appointments) {
    const container = document.getElementById('today-appointments-list');
    if (!container) return;

    const data = appointments || this.getSampleAppointments();

    container.innerHTML = data.map(appt => `
      <div class="appointment-item ${appt.status || 'confirmed'}">
        <div class="appointment-time">${appt.time || formatTime(appt.scheduled_time)}</div>
        <div class="appointment-info">
          <div class="appointment-patient">${escapeHtml(appt.patient_name || 'Patient')}</div>
          <div class="appointment-service">${escapeHtml(appt.service || 'General Checkup')}</div>
        </div>
        <span class="badge badge-${appt.status === 'confirmed' ? 'success' : appt.status === 'pending' ? 'warning' : 'info'}">${appt.status || 'confirmed'}</span>
      </div>
    `).join('');
  },

  /**
   * Initialize dashboard charts with Chart.js
   */
  initCharts() {
    initChartDefaults();

    // Calls this week bar chart
    const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const callsData = [42, 38, 55, 47, 61, 33, 28];
    this.charts.calls = initCallsBarChart('calls-chart', dayLabels, callsData);

    // Top services chart
    const serviceLabels = ['General', 'Cosmetic', 'Implants', 'Ortho', 'Emergency'];
    const serviceData = [145, 89, 67, 52, 38];
    this.charts.services = initServicesHorizontalBarChart('services-chart', serviceLabels, serviceData);
  },

  /**
   * Setup WebSocket for real-time updates
   */
  setupWebSocket() {
    const user = Auth.getUser();
    if (!user) return;

    wsClient.connect(user.clinic_id || 'demo');

    wsClient.onCallUpdate((data) => {
      console.log('Call update:', data);
      showToast(`📞 ${data.type === 'call_started' ? 'Incoming call' : 'Call ended'}: ${data.caller_name || 'Unknown'}`, 'info');
      // Refresh calls list
      this.loadRecentCalls();
    });

    wsClient.onAppointmentUpdate((data) => {
      console.log('Appointment update:', data);
      showToast(`📅 Appointment ${data.type.replace('appointment_', '')}: ${data.patient_name || 'Patient'}`, 'info');
      // Refresh appointments
      this.loadTodayAppointments();
    });
  },

  async loadRecentCalls() {
    try {
      const calls = await API.getRecentCalls();
      this.renderRecentCalls(calls);
    } catch (e) {
      // Keep existing data
    }
  },

  async loadTodayAppointments() {
    try {
      const appts = await API.getTodayAppointments();
      this.renderTodayAppointments(appts);
    } catch (e) {
      // Keep existing data
    }
  },

  /**
   * Sample metrics data (fallback)
   */
  getSampleMetrics() {
    return {
      calls_today: 47,
      calls_trend: '+12%',
      booked_today: 12,
      booked_trend: '+8%',
      revenue_today: 3240,
      revenue_trend: '+15%',
      satisfaction: 96,
      satisfaction_trend: '+2%'
    };
  },

  /**
   * Sample calls data (fallback)
   */
  getSampleCalls() {
    return [
      { id: '1', caller_name: 'Maria Rodriguez', time: '2 min ago', duration: 245, language: 'es', sentiment_emoji: '😊', status: 'completed' },
      { id: '2', caller_name: 'James Wilson', time: '15 min ago', duration: 182, language: 'en', sentiment_emoji: '😊', status: 'completed' },
      { id: '3', caller_name: 'Sofia Martinez', time: '32 min ago', duration: 310, language: 'es', sentiment_emoji: '😐', status: 'completed' },
      { id: '4', caller_name: 'Robert Chen', time: '1h ago', duration: 95, language: 'en', sentiment_emoji: '😊', status: 'completed' },
      { id: '5', caller_name: '(305) 555-0147', time: '2h ago', duration: 0, language: 'en', sentiment_emoji: '😟', status: 'missed' }
    ];
  },

  getSampleAppointments() {
    const stored = localStorage.getItem('renia_appointments');
    if (stored) {
      try {
        const appts = JSON.parse(stored);
        // Filter for May 23, 2026 (demo focus date) and not cancelled
        const todayAppts = appts.filter(a => a.date === '2026-05-23' && a.status !== 'Cancelled');
        if (todayAppts.length > 0) {
          // Sort by time
          return todayAppts.map(a => ({
            patient_name: a.name,
            time: a.time,
            service: a.service,
            status: a.status.toLowerCase()
          }));
        }
      } catch (e) {
        console.warn('Error reading from renia_appointments in dashboard:', e);
      }
    }

    return [
      { patient_name: 'Emily Johnson', time: '9:00 AM', service: 'General Checkup', status: 'confirmed' },
      { patient_name: 'Carlos Hernandez', time: '9:30 AM', service: 'Dental Implant Consult', status: 'confirmed' },
      { patient_name: 'Lisa Thompson', time: '10:00 AM', service: 'Teeth Whitening', status: 'confirmed' },
      { patient_name: 'David Park', time: '11:00 AM', service: 'Orthodontics Follow-up', status: 'pending' },
      { patient_name: 'Ana Garcia', time: '1:30 PM', service: 'Emergency - Toothache', status: 'confirmed' }
    ];
  }
};
