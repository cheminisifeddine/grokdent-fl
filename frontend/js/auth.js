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
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const publicPages = ['index.html', 'signup.html', ''];

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

    let currentStep = 1;
    const totalSteps = 4;

    const showStep = (step) => {
      for (let i = 1; i <= totalSteps; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        if (stepEl) stepEl.classList.toggle('hidden', i !== step);
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
          nextBtn.textContent = '🚀 Launch Your AI Receptionist';
          nextBtn.classList.add('btn-lg');
        } else {
          nextBtn.textContent = 'Next →';
          nextBtn.classList.remove('btn-lg');
        }
      }

      currentStep = step;
    };

    // Back button
    const backBtn = document.getElementById('signup-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        if (currentStep > 1) showStep(currentStep - 1);
      });
    }

    // Next button
    const nextBtn = document.getElementById('signup-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', async () => {
        if (currentStep < totalSteps) {
          showStep(currentStep + 1);

          // If moving to step 4, populate summary
          if (currentStep === 4) {
            Auth.populateSignupSummary();
          }
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
            nextBtn.textContent = '🚀 Launch Your AI Receptionist';
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
      services: Array.from(document.querySelectorAll('#step-2 input[type="checkbox"]:checked')).map(cb => cb.value),
      insurance: Array.from(document.querySelectorAll('#step-3 input[type="checkbox"]:checked')).map(cb => cb.value),
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

    const services = data.services.length ? data.services.join(', ') : 'None selected';
    const insurance = data.insurance.length ? data.insurance.join(', ') : 'None selected';

    summaryEl.innerHTML = `
      <div class="summary-row"><strong>Clinic:</strong> ${escapeHtml(data.clinic_name)}</div>
      <div class="summary-row"><strong>Location:</strong> ${escapeHtml(data.address)}, ${escapeHtml(data.city)}, FL ${escapeHtml(data.zip)}</div>
      <div class="summary-row"><strong>Phone:</strong> ${formatPhone(data.phone)}</div>
      <div class="summary-row"><strong>Services:</strong> ${escapeHtml(services)}</div>
      <div class="summary-row"><strong>Insurance:</strong> ${escapeHtml(insurance)}</div>
      <div class="summary-row"><strong>Admin:</strong> ${escapeHtml(data.email)}</div>
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
