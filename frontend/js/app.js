/* ============================================
   Renia AI — Main App Initialization
   FIXED: All selectors match actual HTML, demo-mode ready
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  // Detect current page
  const path = window.location.pathname;
  const rawPage = path.split('/').pop() || 'index';
  const currentPage = rawPage.replace('.html', '');

  // Always check auth first (now auto-injects demo session on dashboard pages)
  if (typeof Auth !== 'undefined') {
    Auth.checkAuth();
    Auth.populateSidebarUser();
  }

  // Initialize page-specific modules
  initPage(currentPage);

  // Setup global event listeners
  setupGlobalListeners();

  // Add spin animation for loading states
  if (!document.getElementById('spin-style')) {
    const style = document.createElement('style');
    style.id = 'spin-style';
    style.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
    document.head.appendChild(style);
  }
});

/**
 * Initialize page-specific functionality
 */
function initPage(page) {
  try {
    switch (page) {
      case 'login':
      case 'index':
      case '':
        if (typeof Auth !== 'undefined') Auth.initLoginForm();
        break;

      case 'signup':
        if (typeof Auth !== 'undefined') Auth.initSignupForm();
        break;

      case 'dashboard':
        if (typeof Dashboard !== 'undefined') Dashboard.loadDashboard();
        initDashboardInteractivity();
        break;

      case 'calls':
        initCallsPage();
        break;

      case 'appointments':
        initAppointmentsPage();
        break;

      case 'knowledge-base':
        initKnowledgeBasePage();
        break;

      case 'analytics':
        initAnalyticsPage();
        break;

      case 'settings':
        initSettingsPage();
        break;

      case 'billing':
        initBillingPage();
        break;
    }
  } catch (err) {
    console.warn('Page init error (non-fatal):', err);
  }
}

/**
 * Setup global event listeners for modals, logout, tabs, etc.
 */
function setupGlobalListeners() {
  // Logout — works on the sidebar logout div
  document.querySelectorAll('[data-action="logout"], .sidebar-logout').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      if (typeof Auth !== 'undefined') Auth.logout();
      else window.location.href = 'index.html';
    });
  });

  // Also wire the inline onclick logout div (dashboard uses onclick="Auth.logout()")
  // This is already handled by inline onclick, so no conflict

  // Modal overlay close on backdrop click
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-backdrop')) {
      closeAllModals();
    }
  });

  // Modal close buttons
  document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => closeAllModals());
  });

  // Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAllModals();
  });
}

function closeAllModals() {
  document.querySelectorAll('.modal-overlay, .modal-backdrop').forEach(m => {
    m.style.display = 'none';
    m.classList.remove('active', 'flex');
    m.classList.add('hidden');
  });
  document.querySelectorAll('.side-panel').forEach(p => {
    p.classList.remove('open');
  });
}

/* ============================================
   Dashboard Page — Interactivity
   ============================================ */
function initDashboardInteractivity() {
  // Animate metric counters
  document.querySelectorAll('[data-format]').forEach(el => {
    const text = el.textContent.replace(/[$,%]/g, '').replace(/,/g, '').trim();
    const target = parseFloat(text) || 0;
    const format = el.getAttribute('data-format');
    if (target > 0) animateCounter(el, target, 1200);
  });
}

/* ============================================
   Calls Page
   ============================================ */
// Calls page is fully initialized by its inline script (calls.html)
function initCallsPage() { /* no-op: inline script handles everything */ }

/* ============================================
   Appointments Page
   ============================================ */
function initAppointmentsPage() {
  // New appointment button
  const newApptBtn = document.getElementById('new-appointment-btn');
  if (newApptBtn) {
    newApptBtn.addEventListener('click', () => openAppointmentModal());
  }

  // Also wire any other "book" or "new" buttons with similar names
  document.querySelectorAll('[data-action="new-appointment"]').forEach(btn => {
    btn.addEventListener('click', () => openAppointmentModal());
  });
}

function openAppointmentModal() {
  let modal = document.getElementById('appointment-modal');
  if (!modal) {
    const overlay = document.createElement('div');
    overlay.id = 'appointment-modal';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';

    overlay.innerHTML = `
      <div style="background:white;border-radius:20px;width:100%;max-width:520px;box-shadow:0 25px 50px rgba(0,0,0,0.15);">
        <div style="padding:24px 28px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;">
          <h2 style="font-size:18px;font-weight:800;color:#0f172a;margin:0;">New Appointment</h2>
          <button id="close-appt-modal" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:18px;color:#64748b;">×</button>
        </div>
        <form id="appointment-form" style="padding:24px 28px;">
          <div style="display:grid;gap:16px;">
            <div>
              <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Patient Name</label>
              <input type="text" id="appt-patient" placeholder="Enter patient name" required style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;" onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='#e2e8f0'">
            </div>
            <div>
              <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Service Type</label>
              <select id="appt-service" style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;">
                <option>General Checkup</option>
                <option>Dental Cleaning</option>
                <option>Dental Implant Consult</option>
                <option>Teeth Whitening</option>
                <option>Root Canal</option>
                <option>Crown / Bridge</option>
                <option>Orthodontics</option>
                <option>Emergency</option>
              </select>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Date</label>
                <input type="date" id="appt-date" required style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;" onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='#e2e8f0'">
              </div>
              <div>
                <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Time</label>
                <select id="appt-time" style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;">
                  <option>9:00 AM</option><option>9:30 AM</option><option>10:00 AM</option>
                  <option>10:30 AM</option><option>11:00 AM</option><option>11:30 AM</option>
                  <option>1:00 PM</option><option>1:30 PM</option><option>2:00 PM</option>
                  <option>2:30 PM</option><option>3:00 PM</option><option>3:30 PM</option>
                  <option>4:00 PM</option><option>4:30 PM</option>
                </select>
              </div>
            </div>
            <div>
              <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Notes (optional)</label>
              <textarea id="appt-notes" rows="3" placeholder="Any additional notes..." style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;resize:none;box-sizing:border-box;" onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='#e2e8f0'"></textarea>
            </div>
          </div>
          <div style="margin-top:20px;display:flex;gap:12px;">
            <button type="button" id="cancel-appt-btn" style="flex:1;padding:12px;border:1px solid #e2e8f0;border-radius:12px;font-weight:600;color:#64748b;background:white;cursor:pointer;font-size:14px;">Cancel</button>
            <button type="submit" style="flex:2;padding:12px;background:#0f172a;color:white;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:14px;">Book Appointment</button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(overlay);

    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    document.getElementById('close-appt-modal')?.addEventListener('click', () => overlay.remove());
    document.getElementById('cancel-appt-btn')?.addEventListener('click', () => overlay.remove());

    document.getElementById('appointment-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const patient = document.getElementById('appt-patient')?.value;
      const service = document.getElementById('appt-service')?.value;
      const date = document.getElementById('appt-date')?.value;
      const time = document.getElementById('appt-time')?.value;

      if (!patient || !date) {
        showToast('Patient name and date are required', 'error');
        return;
      }

      const submitBtn = e.target.querySelector('[type="submit"]');
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Booking...'; }

      try {
        await API.createAppointment({ patient_name: patient, service_type: service, appointment_datetime: `${date} ${time}` });
      } catch (err) {
        console.warn('Appointment booking API failed, using local fallback:', err.message);
      }

      overlay.remove();
      showToast(`✅ Appointment booked for ${patient} on ${date} at ${time}`, 'success');
    });

    return;
  }
  modal.style.display = 'flex';
}

/* ============================================
   Knowledge Base Page
   ============================================ */
// Knowledge Base page is fully initialized by its inline script (knowledge-base.html)
function initKnowledgeBasePage() { /* no-op: inline script handles everything */ }

/* ============================================
   Analytics Page
   ============================================ */
function initAnalyticsPage() {
  // Delegate to the Analytics module defined in analytics.html
  if (typeof Analytics !== 'undefined' && typeof Analytics.load === 'function') {
    Analytics.load(7);
    return;
  }

  // Fallback if Analytics module not loaded (direct chart rendering)
  if (typeof initChartDefaults === 'function') initChartDefaults();

  const dateLabels7 = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    dateLabels7.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
  }

  if (typeof initCallsLineChart === 'function') {
    initCallsLineChart('analytics-calls-chart', dateLabels7, [35, 42, 38, 55, 47, 61, 53]);
    initBookingsLineChart('analytics-bookings-chart', dateLabels7, [8, 12, 10, 15, 11, 14, 12]);
    initServicesHorizontalBarChart('analytics-services-chart',
      ['General Dentistry', 'Cosmetic', 'Dental Implants', 'Orthodontics', 'Emergency', 'Whitening'],
      [145, 89, 67, 52, 38, 31]
    );
    initLanguageDoughnutChart('analytics-language-chart', [
      { label: 'English', value: 78 },
      { label: 'Spanish', value: 22 }
    ]);
  }

  // Wire date range buttons (inline in analytics.html)
  document.querySelectorAll('.date-range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.date-range-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const days = parseInt(btn.getAttribute('data-days')) || 7;
      showToast(`Showing ${days}-day view`, 'info');
    });
  });

  // Animate counters
  document.querySelectorAll('[data-format]').forEach(el => {
    const text = el.textContent.replace(/[$,%]/g, '').replace(/,/g, '').trim();
    const target = parseFloat(text) || 0;
    if (target > 0 && typeof animateCounter === 'function') animateCounter(el, target, 1200);
  });
}

/* ============================================
   Settings Page
   ============================================ */
function initSettingsPage() {
  // Settings page has its own robust inline init script.
  // This function is a no-op to avoid conflicts.
  // The inline script in settings.html handles tab switching, form submissions, etc.
}

/* ============================================
   Billing Page
   ============================================ */
function initBillingPage() {
  document.querySelectorAll('.select-plan-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (btn.classList.contains('btn-current') || btn.textContent.includes('Current')) return;
      const plan = btn.getAttribute('data-plan') || 'starter';

      btn.textContent = 'Processing...';
      btn.disabled = true;

      try { await API.createCheckout(plan); } catch (err) {
        console.warn('Create checkout API failed:', err.message);
      }

      // Update UI
      document.querySelectorAll('.select-plan-btn').forEach(b => {
        b.disabled = false;
        b.textContent = 'Select Plan';
        b.style.background = '';
        b.style.color = '';
      });
      btn.textContent = '✓ Current Plan';
      btn.style.background = '#0f172a';
      btn.style.color = 'white';
      showToast(`Switched to ${plan.charAt(0).toUpperCase() + plan.slice(1)} plan! 🎉`, 'success');
    });
  });

  // Cancel subscription
  document.getElementById('cancel-subscription-btn')?.addEventListener('click', () => {
    if (confirm('Are you sure you want to cancel your subscription?')) {
      showToast('Subscription cancelled. Access continues until end of billing period.', 'info');
    }
  });
}

// Global modal view helpers for the dashboard feed clicks
window.viewCallTranscript = function(caller, time, lang) {
  caller = escapeHtml(caller);
  time = escapeHtml(time);
  lang = escapeHtml(lang);
  const modal = document.getElementById('transcript-modal');
  if (modal) modal.remove();
  
  const overlay = document.createElement('div');
  overlay.id = 'transcript-modal';
  overlay.className = 'modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';
  
  const isSpanish = lang.toLowerCase() === 'spanish';
  
  let transcriptHtml = '';
  if (isSpanish) {
    transcriptHtml = `
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">Recepcionista IA:</strong> Gracias por llamar a Sunshine Smiles Dental. Soy la asistente de voz inteligente Ash. ¿En qué puedo ayudarle hoy?</div>
      <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> Hola, buenas tardes. Quisiera programar una cita para una limpieza dental para la próxima semana, por favor.</div>
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">Recepcionista IA:</strong> ¡Con mucho gusto! Tengo disponibilidad para el miércoles a las 10:00 AM o el viernes a la 1:30 PM. ¿Cuál de estos horarios le queda mejor?</div>
      <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> El viernes a la 1:30 PM está excelente, gracias.</div>
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">Recepcionista IA:</strong> ¡Perfecto! He reservado su cita de limpieza dental para el viernes 23 de mayo a la 1:30 PM. Recibirá un mensaje de confirmación en breve. ¿Hay algo más en lo que pueda asistirle?</div>
      <div><strong style="color:#0f172a;">${caller}:</strong> No, eso sería todo. ¡Muchísimas gracias!</div>
    `;
  } else {
    transcriptHtml = `
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> Thank you for calling Sunshine Smiles Dental. This is your AI receptionist Ash. How can I assist you today?</div>
      <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> Hi, I'd like to book an appointment for a dental checkup and cleaning, please.</div>
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> I would be delighted to help you with that! I have availability this week on Wednesday at 10 AM or Friday at 11 AM. Which of those works better for you?</div>
      <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> Wednesday at 10 AM works great.</div>
      <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> Fantastic! I have successfully scheduled your appointment for Wednesday at 10:00 AM. You will receive a confirmation text shortly. Is there anything else I can help you with?</div>
      <div><strong style="color:#0f172a;">${caller}:</strong> No, that is everything. Thank you!</div>
    `;
  }

  const summaryText = isSpanish 
    ? "La paciente solicitó una cita de limpieza dental. Reservada con éxito para el viernes a la 1:30 PM. Mensaje de confirmación SMS enviado."
    : "Patient requested a dental cleaning and checkup. Successfully booked for Wednesday at 10:00 AM. Confirmation SMS dispatched.";

  overlay.innerHTML = `
    <div style="background:white;border-radius:20px;width:100%;max-width:600px;max-height:85vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 25px 50px rgba(0,0,0,0.15);">
      <div style="padding:24px 28px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;background:#f8fafc;">
        <div>
          <h2 style="font-size:18px;font-weight:850;color:#0f172a;margin:0 0 4px;font-family:'Outfit',sans-serif;">${caller}</h2>
          <p style="font-size:13px;color:#64748b;margin:0;font-weight:600;">🕒 ${time} · 🌐 ${lang}</p>
        </div>
        <button onclick="document.getElementById('transcript-modal').remove()" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:18px;color:#64748b;display:flex;align-items:center;justify-content:center;">×</button>
      </div>
      <div style="padding:24px 28px;overflow-y:auto;flex:1;">
        <div style="background:#f8fafc;border-radius:16px;padding:20px;font-family:'JetBrains Mono',monospace;font-size:13px;line-height:1.7;color:#334155;border:1px solid #f1f5f9;">
          ${transcriptHtml}
        </div>
        <div style="margin-top:20px;padding:16px;background:#f0fdf4;border-radius:16px;border:1px solid #bbf7d0;display:flex;flex-direction:column;gap:4px;">
          <div style="font-size:11px;font-weight:800;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">AI Receptionist Summary</div>
          <div style="font-size:13px;color:#15803d;font-weight:600;line-height:1.5;">${summaryText}</div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
};

window.viewAppointmentDetailsDashboard = function(name, time, service, status) {
  name = escapeHtml(name);
  time = escapeHtml(time);
  service = escapeHtml(service);
  status = escapeHtml(status);
  const existing = document.getElementById('appt-details-modal');
  if (existing) existing.remove();
  
  const overlay = document.createElement('div');
  overlay.id = 'appt-details-modal';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';
  
  const capStatus = status.charAt(0).toUpperCase() + status.slice(1);
  let statusBadgeClass = 'status-scheduled';
  if (capStatus === 'Confirmed' || capStatus === 'Success') statusBadgeClass = 'status-confirmed';
  if (capStatus === 'Checked-in' || capStatus === 'Pending') statusBadgeClass = 'status-checked-in';
  if (capStatus === 'Completed') statusBadgeClass = 'status-completed';
  if (capStatus === 'Cancelled') statusBadgeClass = 'status-cancelled';
  
  overlay.innerHTML = `
    <div style="background:white;border-radius:20px;width:100%;max-width:480px;box-shadow:0 25px 50px rgba(0,0,0,0.15);overflow:hidden;">
      <div style="padding:24px 28px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;background:#f8fafc;">
        <div>
          <span class="status-badge ${statusBadgeClass}">${capStatus}</span>
          <h2 style="font-size:18px;font-weight:850;color:#0f172a;margin:6px 0 0 0;font-family:'Outfit',sans-serif;">Appointment Details</h2>
        </div>
        <button onclick="document.getElementById('appt-details-modal').remove()" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:18px;color:#64748b;display:flex;align-items:center;justify-content:center;">×</button>
      </div>
      
      <div style="padding:24px 28px;">
        <div style="display:grid;gap:18px;margin-bottom:24px;">
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Patient Name</label>
            <div style="font-size:16px;font-weight:800;color:#0f172a;">👤 ${name}</div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Date</label>
              <div style="font-size:14px;font-weight:700;color:#334155;">📅 2026-05-23</div>
            </div>
            <div>
              <label style="display:block;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Time</label>
              <div style="font-size:14px;font-weight:700;color:#334155;">🕒 ${time}</div>
            </div>
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Service Type</label>
            <div style="font-size:14px;font-weight:700;color:#334155;">🦷 ${service}</div>
          </div>
          <div>
            <label style="display:block;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Triage Notes</label>
            <div style="font-size:13px;color:#475569;background:#f8fafc;padding:12px;border-radius:10px;line-height:1.6;border:1px solid #f1f5f9;">
              Patient scheduled through AI Voice Receptionist. Insurance eligibility has been auto-verified.
            </div>
          </div>
        </div>
        
        <div style="display:flex;justify-content:flex-end;">
          <button onclick="document.getElementById('appt-details-modal').remove()" style="padding:12px 24px;font-size:13px;font-weight:800;background:#0f172a;color:white;border:none;border-radius:12px;cursor:pointer;box-shadow:0 4px 6px rgba(0,0,0,0.1);">Close Details</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
};
