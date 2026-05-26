/* ============================================
   Renia AI — Utility Functions
   ============================================ */

/**
 * Format a date to readable string (e.g., "Jan 15, 2026")
 */
function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
}

/**
 * Format a date to time string (e.g., "2:30 PM")
 */
function formatTime(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';
  let hours = d.getHours();
  const minutes = d.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;
  return `${hours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
}

/**
 * Format duration in seconds to MM:SS (e.g., "3:24")
 */
function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format currency (e.g., "$1,234")
 */
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '$0';
  return '$' + Number(amount).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  });
}

/**
 * Format currency with cents (e.g., "$1,234.56")
 */
function formatCurrencyWithCents(amount) {
  if (amount === null || amount === undefined) return '$0.00';
  return '$' + Number(amount).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Truncate a string to specified length
 */
function truncate(str, len = 50) {
  if (!str) return '';
  if (str.length <= len) return str;
  return str.substring(0, len) + '…';
}

/**
 * Debounce function
 */
function debounce(fn, delay = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
  // Remove existing toasts
  document.querySelectorAll('.renia-toast').forEach(t => t.remove());

  const colors = {
    success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534', icon: '<span class="material-symbols-outlined text-emerald-400 text-[18px]">check_circle</span>' },
    error:   { bg: '#fef2f2', border: '#fecaca', text: '#991b1b', icon: '❌' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#92400e', icon: '⚠️' },
    info:    { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af', icon: 'ℹ️' }
  };
  const c = colors[type] || colors.success;

  const toast = document.createElement('div');
  toast.className = 'renia-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 99999;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    background: ${c.bg};
    border: 1px solid ${c.border};
    color: ${c.text};
    border-radius: 14px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    max-width: 420px;
    animation: toastIn 0.3s cubic-bezier(0.16,1,0.3,1);
  `;
  toast.innerHTML = `<span style="font-size:18px">${c.icon}</span><span>${message}</span>`;
  document.body.appendChild(toast);

  // Inject keyframes once
  if (!document.getElementById('toast-keyframes')) {
    const style = document.createElement('style');
    style.id = 'toast-keyframes';
    style.textContent = '@keyframes toastIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}';
    document.head.appendChild(style);
  }

  setTimeout(() => {
    toast.style.transition = 'all 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(30px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}


/**
 * Animate a counter from 0 to target value
 */
function animateCounter(element, target, duration = 1000) {
  if (!element) return;
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (target - start) * eased);

    // Check if the original text had a $ prefix or % suffix
    const text = element.getAttribute('data-format');
    if (text === 'currency') {
      element.textContent = formatCurrency(current);
    } else if (text === 'percent') {
      element.textContent = current + '%';
    } else {
      element.textContent = current.toLocaleString();
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

/**
 * Generate a random ID string
 */
function generateId() {
  return 'id_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
}

/**
 * Get relative time string (e.g., "5 min ago")
 */
function getRelativeTime(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  const now = new Date();
  const diffMs = now - d;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin} min ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return formatDate(date);
}

/**
 * Parse query parameters from URL
 */
function getQueryParams() {
  const params = {};
  const search = window.location.search.substring(1);
  if (!search) return params;
  search.split('&').forEach(pair => {
    const [key, value] = pair.split('=');
    params[decodeURIComponent(key)] = decodeURIComponent(value || '');
  });
  return params;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Get initials from a name
 */
function getInitials(name) {
  if (!name) return '?';
  return name.split(' ')
    .map(part => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');
}

/**
 * Format phone number
 */
function formatPhone(phone) {
  if (!phone) return '';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return phone;
}

/**
 * Get the day name
 */
function getDayName(date, short = false) {
  const days = short
    ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    : ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  return days[new Date(date).getDay()];
}

/**
 * Sleep helper for async operations
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Clone object deeply
 */
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}
