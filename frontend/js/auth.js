/* ============================================
   Renia AI — Authentication Module
   FIXED: Auto demo mode so dashboard is always accessible
   ============================================ */

const Auth = {
  TOKEN_KEY: 'renia_token',
  USER_KEY: 'renia_user',

  /**
   * Check if user is authenticated.
   * On dashboard pages with no token → inject demo token so the UI works.
   */
  checkAuth() {
    const rawPage = window.location.pathname.split('/').pop() || 'index';
    const currentPage = rawPage.replace('.html', '');
    const publicPages = ['index', 'signup', 'login', ''];

    if (publicPages.includes(currentPage)) {
      // If already logged in on a public page, redirect to dashboard
      if (this.getToken()) {
        window.location.href = 'dashboard.html';
      }
      return;
    }

    // Protected pages: if no token, redirect to login page instead of silently injecting demo token
    if (!this.getToken()) {
      window.location.href = 'login.html';
    }
  },

  /**
   * Inject a demo session so the dashboard is always accessible
   */
  _injectDemoSession() {
    const mockToken = 'demo_token_' + Date.now();
    const mockUser = {
      id: 'usr_demo',
      email: 'demo@sunshinedentalcare.com',
      name: 'Dr. Sarah Mitchell',
      clinic_name: 'Sunshine Dental Care',
      role: 'admin'
    };
    this.setToken(mockToken);
    this.setUser(mockUser);
  },

  /**
   * Login with email and password
   */
  async login(email, password) {
    try {
      const response = await API.login(email, password);
      if (response && response.access_token) {
        this.setToken(response.access_token);
        this.setUser(response.user);
        return { success: true, user: response.user };
      }
      return { success: false, error: 'Invalid email or password.' };
    } catch (error) {
      console.warn('API login failed:', error.message);
      return { success: false, error: error.message || 'Connection failed. Please check if backend is running.' };
    }
  },

  /**
   * Sign up a new clinic
   */
  async signup(data) {
    try {
      const response = await API.signup(data);
      if (response && response.access_token) {
        this.setToken(response.access_token);
        this.setUser(response.user);
        return { success: true, user: response.user };
      }
      return { success: false, error: 'Signup failed. Please check inputs.' };
    } catch (error) {
      console.warn('API signup failed:', error.message);
      return { success: false, error: error.message || 'Connection failed. Please try again.' };
    }
  },

  /**
   * Logout: clear storage and redirect to landing page
   */
  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = 'index.html';
  },

  /**
   * Get stored auth token
   */
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  /**
   * Set auth token
   */
  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  /**
   * Get stored user object
   */
  getUser() {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  /**
   * Set user object
   */
  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  /**
   * Initialize login form
   */
  initLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('login-email');
      const passwordInput = document.getElementById('login-password');
      const errorEl = document.getElementById('login-error');
      const btn = document.getElementById('login-btn');

      if (!emailInput || !passwordInput) return;

      const email = emailInput.value.trim();
      const password = passwordInput.value;

      if (!email || !password) {
        if (errorEl) errorEl.textContent = 'Please enter your email and password.';
        return;
      }

      // Loading state
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.4);border-top-color:white;border-radius:50%;animation:spin 0.7s linear infinite;vertical-align:middle;margin-right:6px;"></span>Signing in...';
      }
      if (errorEl) errorEl.textContent = '';

      const result = await Auth.login(email, password);

      if (result.success) {
        window.location.href = 'dashboard.html';
      } else {
        if (errorEl) errorEl.textContent = result.error;
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Authenticate';
        }
      }
    });

    // Wire up explicit Demo Sandbox Explore Button
    const demoBtn = document.getElementById('demo-btn');
    if (demoBtn) {
      demoBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this._injectDemoSession();
        if (typeof showToast === 'function') {
          showToast('Initializing Demo Sandbox Environment...', 'info');
        }
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 600);
      });
    }
  },

  /**
   * Initialize signup form
   */
  initSignupForm() {
    const form = document.getElementById('signup-form');
    if (!form) return;

    form.addEventListener('submit', (e) => e.preventDefault());

    document.querySelectorAll('.toggle-card').forEach(card => {
      card.addEventListener('click', () => {
        card.classList.toggle('active');
      });
    });

    let currentStep = 1;
    const totalSteps = 4;

    const validateStep = (step) => {
      if (step === 1) {
        const name = document.getElementById('signup-clinic-name')?.value.trim();
        const email = document.getElementById('signup-clinic-email')?.value.trim();
        if (!name) { showToast('Clinic Name is required', 'error'); return false; }
        if (!email) { showToast('Clinic Email is required', 'error'); return false; }
      }
      if (step === 4) {
        const adminEmail = document.getElementById('signup-admin-email')?.value.trim();
        const adminPass = document.getElementById('signup-admin-password')?.value;
        if (!adminEmail || !adminPass) { showToast('Admin Email and Password are required', 'error'); return false; }
        if (adminPass.length < 8) { showToast('Password must be at least 8 characters', 'error'); return false; }
      }
      return true;
    };

    const showStep = (step) => {
      for (let i = 1; i <= totalSteps; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        if (stepEl) {
          if (i === step) {
            stepEl.classList.remove('hidden');
            setTimeout(() => stepEl.classList.add('slide-in'), 10);
          } else {
            stepEl.classList.remove('slide-in');
            stepEl.classList.add('hidden');
          }
        }
      }

      document.querySelectorAll('.signup-step').forEach((el, idx) => {
        el.classList.remove('active', 'completed');
        if (idx + 1 < step) el.classList.add('completed');
        if (idx + 1 === step) el.classList.add('active');
      });

      document.querySelectorAll('.step-connector').forEach((el, idx) => {
        el.classList.toggle('completed', idx + 1 < step);
      });

      const progressFill = document.querySelector('.signup-progress .progress-fill');
      if (progressFill) progressFill.style.width = ((step / totalSteps) * 100) + '%';

      const backBtn = document.getElementById('signup-back');
      if (backBtn) backBtn.style.visibility = step === 1 ? 'hidden' : 'visible';

      const nextBtn = document.getElementById('signup-next');
      if (nextBtn) {
        nextBtn.innerHTML = step === totalSteps ? '🚀 Launch Your AI Receptionist' : 'Next →';
      }

      currentStep = step;
    };

    const backBtn = document.getElementById('signup-back');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) showStep(currentStep - 1);
      });
    }

    const nextBtn = document.getElementById('signup-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (!validateStep(currentStep)) return;

        if (currentStep < totalSteps) {
          if (currentStep + 1 === 4) Auth.populateSignupSummary();
          showStep(currentStep + 1);
        } else {
          nextBtn.disabled = true;
          nextBtn.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.4);border-top-color:white;border-radius:50%;animation:spin 0.7s linear infinite;vertical-align:middle;margin-right:6px;"></span>Setting up...';

          const data = Auth.collectSignupData();
          const result = await Auth.signup(data);

          if (result.success) {
            showToast('Welcome to Renia AI! 🎉', 'success');
            setTimeout(() => { window.location.href = 'dashboard.html'; }, 1500);
          } else {
            showToast(result.error, 'error');
            nextBtn.disabled = false;
            nextBtn.innerHTML = '🚀 Launch Your AI Receptionist';
          }
        }
      });
    }

    showStep(1);
  },

  collectSignupData() {
    return {
      clinic_name: document.getElementById('signup-clinic-name')?.value || '',
      address: document.getElementById('signup-address')?.value || '',
      city: document.getElementById('signup-city')?.value || '',
      zip: document.getElementById('signup-zip')?.value || '',
      phone: document.getElementById('signup-phone')?.value || '',
      clinic_email: document.getElementById('signup-clinic-email')?.value || '',
      services: Array.from(document.querySelectorAll('#step-2 .toggle-card.active')).map(c => c.dataset.value),
      insurance: Array.from(document.querySelectorAll('#step-3 .toggle-card.active')).map(c => c.dataset.value),
      policies: document.getElementById('signup-policies')?.value || '',
      email: document.getElementById('signup-admin-email')?.value || '',
      password: document.getElementById('signup-admin-password')?.value || '',
      full_name: document.getElementById('signup-admin-name')?.value || ''
    };
  },

  populateSignupSummary() {
    const data = this.collectSignupData();
    const summaryEl = document.getElementById('signup-summary');
    if (!summaryEl) return;
    summaryEl.innerHTML = `
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:20px;">
        <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:4px;">${escapeHtml(data.clinic_name) || 'New Clinic'}</div>
        <div style="font-size:13px;color:#64748b;margin-bottom:16px;">${escapeHtml(data.clinic_email)} • ${formatPhone(data.phone)}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:12px;">
            <div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Location</div>
            <div style="font-size:14px;font-weight:700;color:#0f172a;margin-top:4px;">${escapeHtml(data.city) || 'City'}, FL ${escapeHtml(data.zip)}</div>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:12px;">
            <div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Services</div>
            <div style="font-size:14px;font-weight:700;color:#0f172a;margin-top:4px;">${data.services.length} Selected</div>
          </div>
        </div>
      </div>
    `;
  },

  populateSidebarUser() {
    const user = this.getUser();
    if (!user) return;

    // Update any user name displays in the page
    const nameEls = document.querySelectorAll('#user-name-display, .sidebar-user-name');
    nameEls.forEach(el => { if (el) el.textContent = user.full_name || user.name || user.email; });

    const roleEls = document.querySelectorAll('.sidebar-user-role');
    roleEls.forEach(el => { if (el) el.textContent = user.role || 'Admin'; });

    const avatarEls = document.querySelectorAll('.sidebar-user-avatar');
    avatarEls.forEach(el => {
      const displayName = user.full_name || user.name;
      if (el && displayName) {
        const parts = displayName.split(' ');
        el.textContent = (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
      }
    });

    // Inject warning banner if we are in a demo sandbox session
    try { this.injectDemoBanner(); } catch (e) { console.warn(e); }
  },

  injectDemoBanner() {
    const token = this.getToken();
    if (token && token.startsWith('demo_token_')) {
      if (document.getElementById('demo-sandbox-banner')) return;

      const banner = document.createElement('div');
      banner.id = 'demo-sandbox-banner';
      banner.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-amber-500 text-white px-5 py-3 rounded-xl flex items-center gap-3 text-xs font-semibold shadow-2xl border border-amber-400 z-[99999] backdrop-blur-md animate-bounce max-w-[90%] sm:max-w-xl';
      banner.style.animationIterationCount = '3';
      banner.innerHTML = `
        <span class="material-symbols-outlined text-[18px] animate-pulse">warning</span>
        <div class="flex-1">
          <span class="block text-[10px] font-bold uppercase tracking-wider text-amber-100 leading-none mb-0.5">Demo Sandbox Mode Active</span>
          <span class="text-zinc-50 text-[10px] font-normal leading-normal">Your settings are saved locally only. Click below to sign in to your real clinic.</span>
        </div>
        <a href="login.html" onclick="Auth.logout();" class="bg-slate-950 text-white hover:bg-slate-900 px-3 py-1.5 rounded-lg font-bold text-[9px] uppercase tracking-wider transition-all flex items-center gap-1 shadow-sm shrink-0">
          Sign In <span class="material-symbols-outlined text-[11px]">arrow_forward</span>
        </a>
      `;
      document.body.appendChild(banner);
    }
  }
};
