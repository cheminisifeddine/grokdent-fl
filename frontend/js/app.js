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
function initCallsPage() {
  // Search filter
  const searchInput = document.getElementById('call-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(filterCalls, 300));
  }

  // Status filter
  const statusFilter = document.getElementById('call-status-filter');
  if (statusFilter) statusFilter.addEventListener('change', filterCalls);

  // Language filter
  const langFilter = document.getElementById('call-language-filter');
  if (langFilter) langFilter.addEventListener('change', filterCalls);

  // View transcript buttons — open modal
  document.querySelectorAll('.view-transcript-btn').forEach(btn => {
    btn.addEventListener('click', () => openTranscriptModal(btn));
  });

  // Pagination buttons
  document.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.page-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('border', 'border-slate-200', 'text-slate-500');
      });
      btn.classList.add('bg-indigo-600', 'text-white');
      btn.classList.remove('border', 'border-slate-200', 'text-slate-500');
    });
  });
}

function filterCalls() {
  const search = (document.getElementById('call-search')?.value || '').toLowerCase();
  const status = document.getElementById('call-status-filter')?.value || '';
  const language = document.getElementById('call-language-filter')?.value || '';

  document.querySelectorAll('tbody tr[data-status]').forEach(row => {
    const text = row.textContent.toLowerCase();
    const rowStatus = (row.getAttribute('data-status') || '').toLowerCase();
    const rowLang = (row.getAttribute('data-language') || '').toLowerCase();

    const matchSearch = !search || text.includes(search);
    const matchStatus = !status || rowStatus.includes(status.toLowerCase());
    const matchLang = !language || rowLang.includes(language.toLowerCase());

    row.style.display = matchSearch && matchStatus && matchLang ? '' : 'none';
  });
}

function openTranscriptModal(btn) {
  const modal = document.getElementById('transcript-modal');
  if (!modal) {
    // Create a simple transcript modal on the fly
    const overlay = document.createElement('div');
    overlay.id = 'transcript-modal';
    overlay.className = 'modal-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';
    
    const row = btn.closest('tr');
    const caller = row?.querySelector('td:nth-child(2)')?.textContent?.trim() || 'Unknown Caller';
    const time = row?.querySelector('td:nth-child(1)')?.textContent?.trim() || '';
    const lang = row?.querySelector('td:nth-child(4) span')?.textContent?.trim() || 'English';
    const status = row?.querySelector('td:nth-child(6) span')?.textContent?.trim() || '';

    overlay.innerHTML = `
      <div style="background:white;border-radius:20px;width:100%;max-width:600px;max-height:80vh;overflow:auto;box-shadow:0 25px 50px rgba(0,0,0,0.15);">
        <div style="padding:24px 28px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;">
          <div>
            <h2 style="font-size:18px;font-weight:800;color:#0f172a;margin:0 0 4px;">${caller}</h2>
            <p style="font-size:13px;color:#64748b;margin:0;">${time} · ${lang}</p>
          </div>
          <button onclick="document.getElementById('transcript-modal').remove()" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:18px;color:#64748b;display:flex;align-items:center;justify-content:center;">×</button>
        </div>
        <div style="padding:24px 28px;">
          <div style="background:#f8fafc;border-radius:12px;padding:20px;font-family:'JetBrains Mono',monospace;font-size:13px;line-height:1.7;color:#334155;">
            <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> Thank you for calling Sunshine Dental Care. This is your AI receptionist. How can I help you today?</div>
            <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> Hi, I'd like to schedule a dental cleaning appointment, please.</div>
            <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> I'd be happy to help with that! I have availability this week on Wednesday at 10 AM and Thursday at 2 PM. Which works better for you?</div>
            <div style="margin-bottom:12px;"><strong style="color:#0f172a;">${caller}:</strong> Wednesday at 10 works great.</div>
            <div style="margin-bottom:12px;"><strong style="color:#6366f1;">AI Receptionist:</strong> Perfect! I've scheduled a dental cleaning for Wednesday at 10:00 AM. You'll receive a confirmation text shortly. Is there anything else I can help you with?</div>
            <div><strong style="color:#0f172a;">${caller}:</strong> No, that's everything. Thank you!</div>
          </div>
          <div style="margin-top:16px;padding:16px;background:#f0fdf4;border-radius:12px;border:1px solid #bbf7d0;">
            <div style="font-size:12px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">AI Summary</div>
            <div style="font-size:14px;color:#15803d;">Patient requested dental cleaning. Successfully booked for Wednesday at 10:00 AM. Confirmation sent via SMS.</div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    return;
  }
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
}

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
      } catch (err) { /* demo mode */ }

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
function initKnowledgeBasePage() {
  // Category tabs
  document.querySelectorAll('.kb-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.kb-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      filterKBByCategory(tab.getAttribute('data-category') || 'all');
    });
  });

  // Seed defaults
  const seedBtn = document.getElementById('seed-defaults-btn');
  if (seedBtn) {
    seedBtn.addEventListener('click', async () => {
      seedBtn.textContent = 'Loading...';
      try { await API.seedKnowledge(); } catch {}
      showToast('Knowledge base loaded with 8 default entries! ✅', 'success');
      seedBtn.textContent = 'Seed Defaults';
    });
  }

  // Add entry button → open panel
  const addBtn = document.getElementById('add-kb-btn');
  const kbPanel = document.getElementById('kb-panel');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      if (kbPanel) {
        kbPanel.classList.add('open');
        document.getElementById('kb-form')?.reset();
        document.getElementById('kb-panel-title').textContent = 'Add New Entry';
      } else {
        openKBModal();
      }
    });
  }

  // Close panel
  const closePanel = document.getElementById('close-kb-panel');
  if (closePanel && kbPanel) {
    closePanel.addEventListener('click', () => kbPanel.classList.remove('open'));
  }

  // KB form submit
  const kbForm = document.getElementById('kb-form');
  if (kbForm) {
    kbForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        question: document.getElementById('kb-question')?.value,
        answer: document.getElementById('kb-answer')?.value,
        answer_es: document.getElementById('kb-answer-es')?.value,
        category: document.getElementById('kb-category')?.value,
        active: true
      };
      if (!data.question || !data.answer) { showToast('Question and answer are required', 'error'); return; }
      try { await API.createKnowledge(data); } catch {}
      showToast('Knowledge entry saved! ✅', 'success');
      if (kbPanel) kbPanel.classList.remove('open');
      kbForm.reset();
    });
  }

  // Edit buttons
  document.querySelectorAll('.kb-edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.kb-item');
      if (kbPanel) {
        kbPanel.classList.add('open');
        if (document.getElementById('kb-panel-title')) document.getElementById('kb-panel-title').textContent = 'Edit Entry';
        const q = item?.querySelector('.kb-question')?.textContent;
        const a = item?.querySelector('.kb-answer')?.textContent;
        if (q && document.getElementById('kb-question')) document.getElementById('kb-question').value = q;
        if (a && document.getElementById('kb-answer')) document.getElementById('kb-answer').value = a;
      } else {
        const q = item?.querySelector('.kb-question')?.textContent || '';
        const a = item?.querySelector('.kb-answer')?.textContent || '';
        openKBModal(q, a);
      }
    });
  });

  // Delete buttons
  document.querySelectorAll('.kb-delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (confirm('Delete this entry?')) {
        const item = btn.closest('.kb-item');
        if (item) {
          item.style.transition = 'all 0.3s ease';
          item.style.opacity = '0';
          item.style.transform = 'translateX(-20px)';
          setTimeout(() => item.remove(), 300);
          showToast('Entry deleted', 'success');
        }
      }
    });
  });
}

function filterKBByCategory(category) {
  document.querySelectorAll('.kb-item').forEach(item => {
    const match = category === 'all' || item.getAttribute('data-category') === category;
    item.style.display = match ? '' : 'none';
  });
}

function openKBModal(question = '', answer = '') {
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';
  const title = question ? 'Edit Knowledge Entry' : 'Add Knowledge Entry';
  overlay.innerHTML = `
    <div style="background:white;border-radius:20px;width:100%;max-width:560px;max-height:80vh;overflow:auto;box-shadow:0 25px 50px rgba(0,0,0,0.15);">
      <div style="padding:24px 28px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;">
        <h2 style="font-size:18px;font-weight:800;color:#0f172a;margin:0;">${title}</h2>
        <button onclick="this.closest('[style*=fixed]').remove()" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:18px;color:#64748b;">×</button>
      </div>
      <form style="padding:24px 28px;" onsubmit="event.preventDefault();this.closest('[style*=fixed]').remove();showToast('Entry saved!','success');">
        <div style="display:grid;gap:16px;">
          <div>
            <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Category</label>
            <select style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;">
              <option>General</option><option>Hours</option><option>Services</option><option>Insurance</option><option>Pricing</option><option>Emergency</option><option>Policies</option>
            </select>
          </div>
          <div>
            <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Question</label>
            <input type="text" required value="${question.replace(/"/g, '&quot;')}" placeholder="e.g. What are your office hours?" style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;box-sizing:border-box;">
          </div>
          <div>
            <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Answer (English)</label>
            <textarea required rows="4" placeholder="Clear, concise answer..." style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;resize:vertical;box-sizing:border-box;">${answer.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>
          </div>
          <div>
            <label style="display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">Answer (Spanish) <span style="font-weight:400;color:#94a3b8;">optional</span></label>
            <textarea rows="2" placeholder="Respuesta en español..." style="width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;outline:none;resize:none;box-sizing:border-box;"></textarea>
          </div>
        </div>
        <div style="margin-top:20px;display:flex;gap:12px;">
          <button type="button" onclick="this.closest('[style*=fixed]').remove()" style="flex:1;padding:12px;border:1px solid #e2e8f0;border-radius:12px;font-weight:600;color:#64748b;background:white;cursor:pointer;font-size:14px;">Cancel</button>
          <button type="submit" style="flex:2;padding:12px;background:#0f172a;color:white;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:14px;">Save Entry</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

/* ============================================
   Analytics Page
   ============================================ */
function initAnalyticsPage() {
  // Init chart defaults
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
    initLanguageDoughnutChart('language-chart', [
      { label: 'English', value: 78 },
      { label: 'Spanish', value: 22 }
    ]);
    initServicesHorizontalBarChart('top-services-chart',
      ['General Dentistry', 'Cosmetic', 'Dental Implants', 'Orthodontics', 'Emergency', 'Whitening'],
      [145, 89, 67, 52, 38, 31]
    );
  }

  // Date range buttons
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
  // Tab switching
  document.querySelectorAll('[data-tab-target]').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab-target');
      document.querySelectorAll('[data-tab-target]').forEach(t => t.classList.remove('active', 'border-indigo-600', 'text-indigo-600'));
      document.querySelectorAll('[data-tab-content]').forEach(c => c.classList.add('hidden'));
      tab.classList.add('active', 'border-indigo-600', 'text-indigo-600');
      document.querySelector(`[data-tab-content="${target}"]`)?.classList.remove('hidden');
    });
  });

  // Activate first tab by default
  document.querySelector('[data-tab-target]')?.click();

  // Profile form
  document.getElementById('profile-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('[type="submit"]');
    if (btn) { btn.textContent = 'Saving...'; btn.disabled = true; }
    try { await API.updateClinic({ clinic_name: document.getElementById('setting-clinic-name')?.value }); } catch {}
    showToast('Profile saved successfully! ✅', 'success');
    if (btn) { btn.textContent = 'Save Changes'; btn.disabled = false; }
  });

  // Hours form
  document.getElementById('hours-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('[type="submit"]');
    if (btn) { btn.textContent = 'Saving...'; btn.disabled = true; }
    showToast('Office hours updated! ✅', 'success');
    if (btn) { btn.textContent = 'Save Hours'; btn.disabled = false; }
  });

  // Voice settings form
  document.getElementById('voice-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('[type="submit"]');
    if (btn) { btn.textContent = 'Saving...'; btn.disabled = true; }
    try { await API.updateVoiceSettings({ voice: document.getElementById('setting-voice')?.value }); } catch {}
    showToast('Voice settings saved! ✅', 'success');
    if (btn) { btn.textContent = 'Save Voice Settings'; btn.disabled = false; }
  });

  // Emergency form
  document.getElementById('emergency-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    showToast('Emergency settings saved! ✅', 'success');
  });

  // Voice preview buttons
  document.querySelectorAll('.preview-voice-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const voice = btn.getAttribute('data-voice') || 'Ash';
      showToast(`Playing ${voice} voice preview... 🔊`, 'info');
    });
  });
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

      try { await API.createCheckout(plan); } catch {}

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
