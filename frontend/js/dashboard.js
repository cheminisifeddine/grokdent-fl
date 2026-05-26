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

    container.innerHTML = data.map(call => {
      const isSpanish = call.language === 'es';
      const sentiment = call.sentiment_emoji || (call.status === 'missed' ? '😟' : '😊');
      const textStatus = call.status === 'missed' ? 'Missed' : (call.status === 'completed' ? 'Resolved' : 'Booked');
      const badgeColor = call.status === 'missed' ? 'text-rose-700 bg-rose-50 border-rose-100' : 'text-emerald-700 bg-emerald-50 border-emerald-100';

      const callerName = escapeHtml(call.caller_name || call.caller_phone || 'Unknown');
      const callTime = escapeHtml(call.time || '2 min ago');
      const callLang = isSpanish ? 'Spanish' : 'English';
      return `
        <div data-caller="${callerName}" data-time="${callTime}" data-lang="${callLang}" class="call-row p-4 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer group flex items-center justify-between border border-transparent hover:border-slate-200" onclick="Dashboard.openCallTranscript(this)">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center text-lg shadow-sm">${sentiment}</div>
            <div>
              <div class="text-sm font-bold text-brand-900">${escapeHtml(call.caller_name || call.caller_phone || 'Unknown')}</div>
              <div class="text-xs font-semibold text-slate-500 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span> ${call.time || 'Just now'} • <span class="bg-white border border-slate-200 px-1.5 py-0.5 rounded shadow-sm text-[10px] uppercase font-bold text-slate-600">${isSpanish ? 'Spanish' : 'English'}</span>
              </div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm font-bold text-brand-900">${formatDuration(call.duration || 0)}</div>
            <div class="text-[10px] font-bold uppercase ${badgeColor} border px-2 py-0.5 rounded-full mt-1 inline-block">${textStatus}</div>
          </div>
        </div>
      `;
    }).join('');
  },

  /**
   * Render today's appointments list
   */
  renderTodayAppointments(appointments) {
    const container = document.getElementById('today-appointments-list');
    if (!container) return;

    const data = appointments || this.getSampleAppointments();

    container.innerHTML = data.map(appt => {
      const timeVal = appt.time || '9:00 AM';
      const parts = timeVal.split(' ');
      const hour = parts[0] || '9:00';
      const ampm = parts[1] || 'AM';
      
      const isEmergency = appt.service.toLowerCase().includes('emergency');
      const barColor = isEmergency ? 'bg-rose-500' : 'bg-brand-500';
      const borderClass = isEmergency ? 'border-rose-200 bg-rose-50/10' : 'border-slate-200 bg-white';
      const badgeColor = isEmergency ? 'text-rose-700 bg-rose-100 border-rose-200' : 'text-brand-700 bg-brand-50 border-brand-100';
      const label = isEmergency ? 'Urgent' : 'Confirmed';

      const apptName = escapeHtml(appt.patient_name || appt.name || 'Patient');
      const apptTime = escapeHtml(appt.time);
      const apptService = escapeHtml(appt.service);
      const apptStatus = escapeHtml(appt.status || 'confirmed');
      return `
        <div data-name="${apptName}" data-time="${apptTime}" data-service="${apptService}" data-status="${apptStatus}" class="appointment-row flex items-center gap-4 p-4 rounded-xl border ${borderClass} shadow-sm hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden" onclick="Dashboard.openAppointmentDetails(this)">
          <div class="absolute left-0 top-0 bottom-0 w-1 ${barColor}"></div>
          <div class="text-center min-w-[70px]">
            <div class="font-bold text-brand-900 text-lg">${hour}</div>
            <div class="text-xs font-bold text-slate-400 uppercase tracking-widest">${ampm}</div>
          </div>
          <div class="flex-1">
            <div class="font-bold text-brand-900">${escapeHtml(appt.patient_name || appt.name || 'Patient')}</div>
            <div class="text-sm font-semibold text-slate-500">${isEmergency ? '🚨 ' : ''}${escapeHtml(appt.service || 'General Checkup')}</div>
          </div>
          <div class="text-[10px] font-bold uppercase ${badgeColor} border px-2.5 py-1 rounded-full">${label}</div>
        </div>
      `;
    }).join('');
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
    const stored = localStorage.getItem('renia_metrics');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {}
    } else {
      const defaults = {
        calls_today: 47,
        calls_trend: '+12%',
        booked_today: 12,
        booked_trend: '+8%',
        revenue_today: 3240,
        revenue_trend: '+15%',
        satisfaction: 96,
        satisfaction_trend: '+2%'
      };
      localStorage.setItem('renia_metrics', JSON.stringify(defaults));
      return defaults;
    }
  },

  /**
   * Sample calls data (fallback)
   */
  getSampleCalls() {
    const stored = localStorage.getItem('renia_calls');
    let custom = [];
    if (stored) {
      try {
        custom = JSON.parse(stored);
      } catch (e) {}
    }
    const defaults = [
      { id: '1', caller_name: 'Maria Rodriguez', time: '2 min ago', duration: 245, language: 'es', sentiment_emoji: '😊', status: 'completed' },
      { id: '2', caller_name: 'James Wilson', time: '15 min ago', duration: 182, language: 'en', sentiment_emoji: '😊', status: 'completed' },
      { id: '3', caller_name: 'Sofia Martinez', time: '32 min ago', duration: 310, language: 'es', sentiment_emoji: '😐', status: 'completed' },
      { id: '4', caller_name: 'Robert Chen', time: '1h ago', duration: 95, language: 'en', sentiment_emoji: '😊', status: 'completed' },
      { id: '5', caller_name: '(305) 555-0147', time: '2h ago', duration: 0, language: 'en', sentiment_emoji: '😟', status: 'missed' }
    ];
    return [...custom, ...defaults];
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

Dashboard.openCallTranscript = function(el) {
  const name = el.getAttribute('data-caller') || 'Unknown';
  const time = el.getAttribute('data-time') || '';
  const lang = el.getAttribute('data-lang') || 'English';
  window.viewCallTranscript(name, time, lang);
};

Dashboard.openAppointmentDetails = function(el) {
  const name = el.getAttribute('data-name') || 'Patient';
  const time = el.getAttribute('data-time') || '';
  const service = el.getAttribute('data-service') || '';
  const status = el.getAttribute('data-status') || 'confirmed';
  window.viewAppointmentDetailsDashboard(name, time, service, status);
};

window.viewCallTranscript = function(name, time, lang) {
  const modalHtml = `
    <div id="call-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div class="bg-slate-900 border border-white/10 rounded-2xl shadow-glow w-full max-w-md overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-slate-950/40">
          <div>
            <h3 class="font-bold text-white">Call Details</h3>
            <div class="text-xs text-slate-400">\${time} • \${lang}</div>
          </div>
          <button onclick="document.getElementById('call-modal').remove()" class="text-slate-400 hover:text-white transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh] custom-scrollbar">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xl">👤</div>
            <div>
              <div class="font-bold text-lg text-white">\${escapeHtml(name)}</div>
              <div class="text-sm text-emerald-400 font-semibold">Resolved Successfully</div>
            </div>
          </div>
          <div class="space-y-4">
            <div class="bg-white/5 p-4 rounded-xl border border-white/5 text-sm text-slate-200">
              <span class="font-bold text-indigo-400">AI Receptionist:</span> Thank you for calling Sunshine Smiles Dental. How can I help you?
            </div>
            <div class="bg-indigo-500/10 p-4 rounded-xl border border-indigo-500/20 text-sm text-slate-200">
              <span class="font-bold text-slate-350">Patient:</span> I'd like to book an appointment.
            </div>
            <div class="bg-white/5 p-4 rounded-xl border border-white/5 text-sm text-slate-200">
              <span class="font-bold text-indigo-400">AI Receptionist:</span> I can help with that. Are you an existing patient?
            </div>
            <div class="bg-indigo-500/10 p-4 rounded-xl border border-indigo-500/20 text-sm text-slate-200">
              <span class="font-bold text-slate-350">Patient:</span> Yes, my name is \${escapeHtml(name)}.
            </div>
            <div class="text-center text-xs font-bold text-slate-500 uppercase tracking-widest mt-4">End of Transcript</div>
          </div>
        </div>
      </div>
    </div>
  `;
  const div = document.createElement('div');
  div.innerHTML = modalHtml;
  document.body.appendChild(div.firstElementChild);
};

window.viewAppointmentDetailsDashboard = function(name, time, service, status) {
  const isEmergency = service.toLowerCase().includes('emergency');
  const badgeClass = isEmergency ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
  const modalHtml = `
    <div id="appt-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div class="bg-slate-900 border border-white/10 rounded-2xl shadow-glow w-full max-w-sm overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-slate-950/40">
          <h3 class="font-bold text-white">Appointment Details</h3>
          <button onclick="document.getElementById('appt-modal').remove()" class="text-slate-400 hover:text-white transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6">
          <div class="flex flex-col items-center text-center mb-6">
            <div class="w-16 h-16 rounded-full bg-white/5 border border-white/10 shadow-sm flex items-center justify-center text-2xl mb-3">📅</div>
            <h2 class="font-bold text-xl text-white">\${escapeHtml(name)}</h2>
            <div class="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase mt-2 \${badgeClass}">\${status}</div>
          </div>
          <div class="space-y-3">
            <div class="flex justify-between items-center py-2 border-b border-white/5">
              <span class="text-sm text-slate-400 font-medium">Service</span>
              <span class="text-sm font-bold text-slate-200">\${escapeHtml(service)}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-white/5">
              <span class="text-sm text-slate-400 font-medium">Time</span>
              <span class="text-sm font-bold text-slate-200">\${time}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-white/5">
              <span class="text-sm text-slate-400 font-medium">Provider</span>
              <span class="text-sm font-bold text-slate-200">Dr. Sarah M.</span>
            </div>
          </div>
          <button onclick="document.getElementById('appt-modal').remove()" class="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl py-3 font-bold text-sm transition-all active:scale-[0.98]">
            Close Details
          </button>
        </div>
      </div>
    </div>
  `;
  const div = document.createElement('div');
  div.innerHTML = modalHtml;
  document.body.appendChild(div.firstElementChild);
};
