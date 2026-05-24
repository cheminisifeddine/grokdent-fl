/* ============================================
   Renia AI — Authentication Module
   ============================================ */

const Auth = {
  TOKEN_KEY: 'renia_token',
  USER_KEY: 'renia_user',

  /**
   * Check if user is authenticated. Redirect if not.
   * Skip redirect on login and signup pages.
   */
  checkAuth() {
    const rawPage = window.location.pathname.split('/').pop() || 'index';
    const currentPage = rawPage.replace('.html', '');
    const publicPages = ['index', 'signup', 'login', ''];

    if (publicPages.includes(currentPage)) {
      // If already logged in, redirect to dashboard
      if (this.getToken()) {
        window.location.href = 'dashboard.html';
      }
      return;
    }

    // Protected pages: redirect to login if no token
    if (!this.getToken()) {
      window.location.href = 'index.html';
    }
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
      return { success: false, error: 'Invalid credentials' };
    } catch (error) {
      console.error('Login error:', error);
      // For demo purposes, allow mock login
      if (email && password) {
        const mockUser = {
          id: 'usr_demo',
          email: email,
          name: 'Dr. Sarah Mitchell',
          clinic_name: 'Sunshine Dental Care',
          role: 'admin'
        };
        const mockToken = 'demo_token_' + Date.now();
        this.setToken(mockToken);
        this.setUser(mockUser);
        return { success: true, user: mockUser };
      }
      return { success: false, error: error.message || 'Login failed. Please try again.' };
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
      return { success: false, error: 'Signup failed' };
    } catch (error) {
      console.error('Signup error:', error);
      // For demo, allow mock signup
      if (data.email && data.password) {
        const mockUser = {
          id: 'usr_' + generateId(),
          email: data.email,
          name: data.admin_name || 'Admin',
          clinic_name: data.clinic_name || 'New Clinic',
          role: 'admin'
        };
        const mockToken = 'demo_token_' + Date.now();
        this.setToken(mockToken);
        this.setUser(mockUser);
        return { success: true, user: mockUser };
      }
      return { success: false, error: error.message || 'Signup failed. Please try again.' };
    }
  },

  /**
   * Logout: clear storage and redirect
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
   * Initialize login form event listeners
   */
  initLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;
      const errorEl = document.getElementById('login-error');
      const btn = document.getElementById('login-btn');

      if (!email || !password) {
        if (errorEl) errorEl.textContent = 'Please enter email and password.';
        return;
      }

      // Show loading state
      btn.disabled = true;
      btn.innerHTML = '<div class="spinner spinner-sm" style="display:inline-block;"></div> Signing in...';
      if (errorEl) errorEl.textContent = '';

      const result = await Auth.login(email, password);

      if (result.success) {
        window.location.href = 'dashboard.html';
      } else {
        if (errorEl) errorEl.textContent = result.error;
        btn.disabled = false;
        btn.textContent = 'Sign In';
      }
    });
  },

  /**
   * Initialize signup form event listeners
   */
  initSignupForm() {
    const form = document.getElementById('signup-form');
    if (!form) return;

    // Prevent default form submission on enter
    form.addEventListener('submit', (e) => e.preventDefault());

    // Initialize toggle cards
    document.querySelectorAll('.toggle-card').forEach(card => {
      card.addEventListener('click', () => {
        card.classList.toggle('active');
      });
    });

    let currentStep = 1;
    const totalSteps = 4;

    const validateStep = (step) => {
      if (step === 1) {
        const name = document.getElementById('signup-clinic-name').value.trim();
        const email = document.getElementById('signup-clinic-email').value.trim();
        if (!name) {
          showToast('Clinic Name is required', 'error');
          return false;
        }
        if (!email) {
          showToast('Clinic Email is required', 'error');
          return false;
        }
      }
      if (step === 4) {
        const adminEmail = document.getElementById('signup-admin-email').value.trim();
        const adminPass = document.getElementById('signup-admin-password').value;
        if (!adminEmail || !adminPass) {
          showToast('Admin Email and Password are required', 'error');
          return false;
        }
        if (adminPass.length < 8) {
          showToast('Password must be at least 8 characters', 'error');
          return false;
        }
      }
      return true;
    };

    const showStep = (step) => {
      for (let i = 1; i <= totalSteps; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        if (stepEl) {
          if (i === step) {
            stepEl.classList.remove('hidden');
            // Slight delay to trigger CSS transition
            setTimeout(() => stepEl.classList.add('slide-in'), 10);
          } else {
            stepEl.classList.remove('slide-in');
            stepEl.classList.add('hidden');
          }
        }
      }

      // Update step indicators
      document.querySelectorAll('.signup-step').forEach((el, idx) => {
        el.classList.remove('active', 'completed');
        if (idx + 1 < step) el.classList.add('completed');
        if (idx + 1 === step) el.classList.add('active');
      });

      // Update connectors
      document.querySelectorAll('.step-connector').forEach((el, idx) => {
        el.classList.toggle('completed', idx + 1 < step);
      });

      // Update progress bar
      const progressFill = document.querySelector('.signup-progress .progress-fill');
      if (progressFill) {
        progressFill.style.width = ((step / totalSteps) * 100) + '%';
      }

      // Toggle back button
      const backBtn = document.getElementById('signup-back');
      if (backBtn) backBtn.style.visibility = step === 1 ? 'hidden' : 'visible';

      // Toggle next/submit button
      const nextBtn = document.getElementById('signup-next');
      if (nextBtn) {
        if (step === totalSteps) {
          nextBtn.innerHTML = '🚀 Launch Your AI Receptionist';
          nextBtn.classList.add('btn-lg');
        } else {
          nextBtn.innerHTML = 'Next &rarr;';
          nextBtn.classList.remove('btn-lg');
        }
      }

      currentStep = step;
    };

    // Back button
    const backBtn = document.getElementById('signup-back');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) showStep(currentStep - 1);
      });
    }

    // Next button
    const nextBtn = document.getElementById('signup-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        if (!validateStep(currentStep)) return;

        if (currentStep < totalSteps) {
          // Calculate the next step summary if going to step 4
          if (currentStep + 1 === 4) {
            Auth.populateSignupSummary();
          }
          showStep(currentStep + 1);
        } else {
          // Submit signup
          nextBtn.disabled = true;
          nextBtn.innerHTML = '<div class="spinner spinner-sm" style="display:inline-block;"></div> Setting up...';

          const data = Auth.collectSignupData();
          const result = await Auth.signup(data);

          if (result.success) {
            showToast('Welcome to Renia AI! 🎉', 'success');
            setTimeout(() => {
              window.location.href = 'dashboard.html';
            }, 1500);
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

  /**
   * Collect all signup form data
   */
  collectSignupData() {
    return {
      clinic_name: document.getElementById('signup-clinic-name')?.value || '',
      address: document.getElementById('signup-address')?.value || '',
      city: document.getElementById('signup-city')?.value || '',
      zip: document.getElementById('signup-zip')?.value || '',
      phone: document.getElementById('signup-phone')?.value || '',
      clinic_email: document.getElementById('signup-clinic-email')?.value || '',
      services: Array.from(document.querySelectorAll('#step-2 .toggle-card.active')).map(card => card.dataset.value),
      insurance: Array.from(document.querySelectorAll('#step-3 .toggle-card.active')).map(card => card.dataset.value),
      policies: document.getElementById('signup-policies')?.value || '',
      email: document.getElementById('signup-admin-email')?.value || '',
      password: document.getElementById('signup-admin-password')?.value || '',
      admin_name: document.getElementById('signup-admin-name')?.value || ''
    };
  },

  /**
   * Populate the signup summary on step 4
   */
  populateSignupSummary() {
    const data = this.collectSignupData();
    const summaryEl = document.getElementById('signup-summary');
    if (!summaryEl) return;

    const servicesCount = data.services.length;
    const insuranceCount = data.insurance.length;

    summaryEl.innerHTML = `
      <div class="summary-dashboard">
        <div class="summary-header">
          <div class="summary-clinic-name">${escapeHtml(data.clinic_name) || 'New Clinic'}</div>
          <div class="summary-clinic-contact">${escapeHtml(data.clinic_email)} &bull; ${formatPhone(data.phone)}</div>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-card-icon">📍</div>
            <div class="summary-card-label">Location</div>
            <div class="summary-card-value">${escapeHtml(data.city) || 'City'}, FL ${escapeHtml(data.zip)}</div>
          </div>
          <div class="summary-card">
            <div class="summary-card-icon">🦷</div>
            <div class="summary-card-label">Services</div>
            <div class="summary-card-value">${servicesCount} Selected</div>
          </div>
          <div class="summary-card">
            <div class="summary-card-icon">🏥</div>
            <div class="summary-card-label">Insurance</div>
            <div class="summary-card-value">${insuranceCount} Selected</div>
          </div>
          <div class="summary-card">
            <div class="summary-card-icon">👤</div>
            <div class="summary-card-label">Admin User</div>
            <div class="summary-card-value" style="word-break: break-all;">${escapeHtml(data.email)}</div>
          </div>
        </div>
      </div>
    `;
  },

  /**
   * Populate sidebar user info
   */
  populateSidebarUser() {
    const user = this.getUser();
    if (!user) return;

    const nameEl = document.querySelector('.sidebar-user-name');
    const roleEl = document.querySelector('.sidebar-user-role');
    const avatarEl = document.querySelector('.sidebar-user-avatar');

    if (nameEl) nameEl.textContent = user.name || user.email;
    if (roleEl) roleEl.textContent = user.role || 'Admin';
    if (avatarEl) avatarEl.textContent = getInitials(user.name || user.email);
  }
};
