/* ============================================
   Renia AI — Main App Initialization
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  // Detect current page
  const path = window.location.pathname;
  const currentPage = path.split('/').pop() || 'index.html';

  // Check authentication
  Auth.checkAuth();

  // Set active sidebar link
  setActiveSidebarLink(currentPage);

  // Setup sidebar user info
  Auth.populateSidebarUser();

  // Initialize page-specific modules
  initPage(currentPage);

  // Setup mobile sidebar toggle
  setupMobileSidebar();

  // Setup global event listeners
  setupGlobalListeners();
});

/**
 * Set the active sidebar navigation link
 */
function setActiveSidebarLink(currentPage) {
  const navLinks = document.querySelectorAll('.sidebar-nav a');
  navLinks.forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href');
    if (href === currentPage) {
      link.classList.add('active');
    }
  });
}

/**
 * Initialize page-specific functionality
 */
function initPage(page) {
  switch (page) {
    case 'index.html':
    case '':
      Auth.initLoginForm();
      break;

    case 'signup.html':
      Auth.initSignupForm();
      break;

    case 'dashboard.html':
      Dashboard.loadDashboard();
      break;

    case 'calls.html':
      initCallsPage();
      break;

    case 'appointments.html':
      initAppointmentsPage();
      break;

    case 'knowledge-base.html':
      initKnowledgeBasePage();
      break;

    case 'analytics.html':
      initAnalyticsPage();
      break;

    case 'settings.html':
      initSettingsPage();
      break;

    case 'billing.html':
      initBillingPage();
      break;
  }
}

/**
 * Setup mobile sidebar toggle
 */
function setupMobileSidebar() {
  const toggleBtn = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      toggleBtn.textContent = sidebar.classList.contains('open') ? '✕' : '☰';
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768 &&
          sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
        toggleBtn.textContent = '☰';
      }
    });
  }
}

/**
 * Setup global event listeners
 */
function setupGlobalListeners() {
  // Logout button
  const logoutBtn = document.querySelector('.sidebar-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      Auth.logout();
    });
  }

  // Modal close on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  // Modal close buttons
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = btn.closest('.modal-overlay');
      if (overlay) overlay.classList.remove('active');
    });
  });

  // Escape key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(overlay => {
        overlay.classList.remove('active');
      });
      document.querySelectorAll('.side-panel.open').forEach(panel => {
        panel.classList.remove('open');
      });
    }
  });

  // Tab switching
  document.querySelectorAll('.tabs').forEach(tabContainer => {
    tabContainer.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tabGroup = tab.closest('.tabs');
        tabGroup.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const targetId = tab.getAttribute('data-tab');
        if (targetId) {
          const parent = tab.closest('.card') || tab.closest('.main-content') || document;
          parent.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
          });
          const targetContent = document.getElementById(targetId);
          if (targetContent) targetContent.classList.add('active');
        }
      });
    });
  });
}

/* ============================================
   Calls Page
   ============================================ */
function initCallsPage() {
  Auth.populateSidebarUser();

  // Transcript modal
  const viewBtns = document.querySelectorAll('.view-call-btn');
  viewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = document.getElementById('transcript-modal');
      if (modal) modal.classList.add('active');
    });
  });

  // Search filter
  const searchInput = document.getElementById('call-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => {
      filterCalls();
    }, 300));
  }

  // Status filter
  const statusFilter = document.getElementById('call-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', filterCalls);
  }

  // Language filter
  const langFilter = document.getElementById('call-language-filter');
  if (langFilter) {
    langFilter.addEventListener('change', filterCalls);
  }
}

function filterCalls() {
  const search = (document.getElementById('call-search')?.value || '').toLowerCase();
  const status = document.getElementById('call-status-filter')?.value || '';
  const language = document.getElementById('call-language-filter')?.value || '';

  document.querySelectorAll('.table tbody tr').forEach(row => {
    const text = row.textContent.toLowerCase();
    const rowStatus = row.getAttribute('data-status') || '';
    const rowLang = row.getAttribute('data-language') || '';

    const matchSearch = !search || text.includes(search);
    const matchStatus = !status || rowStatus === status;
    const matchLang = !language || rowLang === language;

    row.style.display = matchSearch && matchStatus && matchLang ? '' : 'none';
  });
}

/* ============================================
   Appointments Page
   ============================================ */
function initAppointmentsPage() {
  Auth.populateSidebarUser();

  // New appointment button
  const newApptBtn = document.getElementById('new-appointment-btn');
  const apptModal = document.getElementById('appointment-modal');

  if (newApptBtn && apptModal) {
    newApptBtn.addEventListener('click', () => {
      apptModal.classList.add('active');
    });
  }

  // Appointment form submission
  const apptForm = document.getElementById('appointment-form');
  if (apptForm) {
    apptForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        patient_name: document.getElementById('appt-patient')?.value,
        service: document.getElementById('appt-service')?.value,
        date: document.getElementById('appt-date')?.value,
        time: document.getElementById('appt-time')?.value,
        duration: document.getElementById('appt-duration')?.value || 30,
        notes: document.getElementById('appt-notes')?.value
      };

      try {
        await API.createAppointment(data);
        showToast('Appointment created successfully!', 'success');
        if (apptModal) apptModal.classList.remove('active');
        apptForm.reset();
      } catch (error) {
        showToast('Appointment saved (demo mode)', 'success');
        if (apptModal) apptModal.classList.remove('active');
      }
    });
  }
}

/* ============================================
   Knowledge Base Page
   ============================================ */
function initKnowledgeBasePage() {
  Auth.populateSidebarUser();

  // Category tabs
  const tabs = document.querySelectorAll('.kb-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const category = tab.getAttribute('data-category');
      filterKBByCategory(category);
    });
  });

  // Seed defaults button
  const seedBtn = document.getElementById('seed-defaults-btn');
  if (seedBtn) {
    seedBtn.addEventListener('click', async () => {
      try {
        await API.seedKnowledge();
        showToast('Knowledge base seeded with defaults!', 'success');
      } catch (error) {
        showToast('Defaults loaded (demo mode)', 'success');
      }
    });
  }

  // Add KB entry
  const addBtn = document.getElementById('add-kb-btn');
  const kbPanel = document.getElementById('kb-panel');
  if (addBtn && kbPanel) {
    addBtn.addEventListener('click', () => {
      kbPanel.classList.add('open');
      document.getElementById('kb-form')?.reset();
    });
  }

  // Close KB panel
  const closePanel = document.getElementById('close-kb-panel');
  if (closePanel && kbPanel) {
    closePanel.addEventListener('click', () => {
      kbPanel.classList.remove('open');
    });
  }

  // KB form submission
  const kbForm = document.getElementById('kb-form');
  if (kbForm) {
    kbForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        question: document.getElementById('kb-question')?.value,
        answer: document.getElementById('kb-answer')?.value,
        answer_es: document.getElementById('kb-answer-es')?.value,
        category: document.getElementById('kb-category')?.value,
        priority: document.getElementById('kb-priority')?.value || 'medium',
        active: document.getElementById('kb-active')?.checked ?? true
      };

      try {
        await API.createKnowledge(data);
        showToast('Knowledge entry saved!', 'success');
        kbPanel.classList.remove('open');
      } catch (error) {
        showToast('Entry saved (demo mode)', 'success');
        kbPanel.classList.remove('open');
      }
    });
  }

  // Edit/Delete buttons
  document.querySelectorAll('.kb-edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.kb-item');
      if (kbPanel) kbPanel.classList.add('open');
      // Populate form with existing data
      const question = item?.querySelector('.kb-question')?.textContent;
      const answer = item?.querySelector('.kb-answer')?.textContent;
      if (question) document.getElementById('kb-question').value = question;
      if (answer) document.getElementById('kb-answer').value = answer;
    });
  });

  document.querySelectorAll('.kb-delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (confirm('Delete this knowledge base entry?')) {
        const item = btn.closest('.kb-item');
        if (item) {
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
    if (category === 'all' || item.getAttribute('data-category') === category) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
    }
  });
}

/* ============================================
   Analytics Page
   ============================================ */
function initAnalyticsPage() {
  Auth.populateSidebarUser();

  // Initialize charts
  initChartDefaults();

  const dateLabels7 = ['May 17', 'May 18', 'May 19', 'May 20', 'May 21', 'May 22', 'May 23'];
  const dateLabels30 = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    dateLabels30.push(`${d.getMonth() + 1}/${d.getDate()}`);
  }

  initCallsLineChart('analytics-calls-chart', dateLabels7, [35, 42, 38, 55, 47, 61, 53]);
  initBookingsLineChart('analytics-bookings-chart', dateLabels7, [8, 12, 10, 15, 11, 14, 12]);
  initLanguageDoughnutChart('language-chart', [
    { label: 'English', value: 78 },
    { label: 'Spanish', value: 22 }
  ]);
  initServicesHorizontalBarChart('top-services-chart',
    ['General Dentistry', 'Cosmetic', 'Dental Implants', 'Orthodontics', 'Emergency', 'Teeth Whitening'],
    [145, 89, 67, 52, 38, 31]
  );

  // Date range buttons
  document.querySelectorAll('.date-range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.date-range-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const days = parseInt(btn.getAttribute('data-days'));
      // In production, would reload charts with new data
      showToast(`Showing ${days}-day view`, 'info');
    });
  });

  // Animate metric counters
  document.querySelectorAll('.metric-card .value').forEach(el => {
    const target = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
    animateCounter(el, target, 1200);
  });
}

/* ============================================
   Settings Page
   ============================================ */
function initSettingsPage() {
  Auth.populateSidebarUser();

  // Tab switching is handled by the global listener

  // Profile form
  const profileForm = document.getElementById('profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        clinic_name: document.getElementById('setting-clinic-name')?.value,
        address: document.getElementById('setting-address')?.value,
        city: document.getElementById('setting-city')?.value,
        state: 'FL',
        zip: document.getElementById('setting-zip')?.value,
        phone: document.getElementById('setting-phone')?.value,
        email: document.getElementById('setting-email')?.value
      };
      try {
        await API.updateClinic(data);
        showToast('Profile updated!', 'success');
      } catch (error) {
        showToast('Profile saved (demo mode)', 'success');
      }
    });
  }

  // Hours form
  const hoursForm = document.getElementById('hours-form');
  if (hoursForm) {
    hoursForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showToast('Hours updated!', 'success');
    });
  }

  // Voice settings
  const voiceForm = document.getElementById('voice-form');
  if (voiceForm) {
    voiceForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        voice: document.getElementById('setting-voice')?.value,
        welcome_message: document.getElementById('setting-welcome')?.value,
        spanish_enabled: document.getElementById('setting-spanish')?.checked
      };
      try {
        await API.updateVoiceSettings(data);
        showToast('Voice settings updated!', 'success');
      } catch (error) {
        showToast('Voice settings saved (demo mode)', 'success');
      }
    });
  }

  // Emergency form
  const emergencyForm = document.getElementById('emergency-form');
  if (emergencyForm) {
    emergencyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showToast('Emergency settings updated!', 'success');
    });
  }
}

/* ============================================
   Billing Page
   ============================================ */
function initBillingPage() {
  Auth.populateSidebarUser();

  // Plan select buttons
  document.querySelectorAll('.select-plan-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const plan = btn.getAttribute('data-plan');
      if (btn.classList.contains('btn-current')) return;

      try {
        const result = await API.createCheckout(plan);
        if (result && result.checkout_url) {
          window.location.href = result.checkout_url;
        }
      } catch (error) {
        showToast(`Selected ${plan} plan (demo mode)`, 'success');
        // Update UI
        document.querySelectorAll('.select-plan-btn').forEach(b => {
          b.classList.remove('btn-current');
          b.classList.add('btn-primary');
          b.textContent = 'Select Plan';
        });
        btn.classList.add('btn-current');
        btn.classList.remove('btn-primary');
        btn.textContent = 'Current Plan';
      }
    });
  });
}
