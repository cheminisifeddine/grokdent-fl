/* ============================================
   Renia AI — Chart Module (Chart.js)
   ============================================ */

// Chart.js global defaults for dark theme
function initChartDefaults() {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded');
    return;
  }

  Chart.defaults.color = '#8888a0';
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(18, 18, 26, 0.95)';
  Chart.defaults.plugins.tooltip.titleColor = '#f0f0f5';
  Chart.defaults.plugins.tooltip.bodyColor = '#8888a0';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.cornerRadius = 10;
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.displayColors = false;
  Chart.defaults.scale.grid = Chart.defaults.scale.grid || {};
  Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.04)';
}

/**
 * Create a gradient fill for charts
 */
function createGradient(ctx, color1, color2, height = 300) {
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, color1);
  gradient.addColorStop(1, color2);
  return gradient;
}

/**
 * Initialize a bar chart for calls data
 */
function initCallsBarChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');
  const gradient = createGradient(ctx, 'rgba(13, 148, 136, 0.8)', 'rgba(13, 148, 136, 0.1)');

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Calls',
        data: data,
        backgroundColor: gradient,
        borderColor: 'rgba(13, 148, 136, 0.9)',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
        maxBarThickness: 40
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y} calls`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8888a0' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#8888a0',
            stepSize: 10
          }
        }
      }
    }
  });
}

/**
 * Initialize a line chart for calls over time
 */
function initCallsLineChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');
  const gradient = createGradient(ctx, 'rgba(13, 148, 136, 0.3)', 'rgba(13, 148, 136, 0.01)');

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Calls',
        data: data,
        borderColor: '#0d9488',
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#0d9488',
        pointBorderColor: '#0a0a0f',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y} calls`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8888a0' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8888a0' }
        }
      }
    }
  });
}

/**
 * Initialize a line chart for bookings over time
 */
function initBookingsLineChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');
  const gradient = createGradient(ctx, 'rgba(249, 115, 22, 0.3)', 'rgba(249, 115, 22, 0.01)');

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Bookings',
        data: data,
        borderColor: '#f97316',
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#f97316',
        pointBorderColor: '#0a0a0f',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y} bookings`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8888a0' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8888a0' }
        }
      }
    }
  });
}

/**
 * Initialize a doughnut chart for language breakdown
 */
function initLanguageDoughnutChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');
  const labels = data.map(d => d.label || d.language);
  const values = data.map(d => d.value || d.count);

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          'rgba(13, 148, 136, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(59, 130, 246, 0.8)'
        ],
        borderColor: [
          'rgba(13, 148, 136, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(139, 92, 246, 1)',
          'rgba(59, 130, 246, 1)'
        ],
        borderWidth: 1,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            pointStyleWidth: 10,
            color: '#8888a0'
          }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = ((ctx.parsed / total) * 100).toFixed(1);
              return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * Initialize a horizontal bar chart for top services
 */
function initServicesHorizontalBarChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');

  const colors = [
    'rgba(13, 148, 136, 0.8)',
    'rgba(249, 115, 22, 0.7)',
    'rgba(139, 92, 246, 0.7)',
    'rgba(59, 130, 246, 0.7)',
    'rgba(16, 185, 129, 0.7)',
    'rgba(245, 158, 11, 0.7)',
    'rgba(236, 72, 153, 0.7)',
    'rgba(99, 102, 241, 0.7)'
  ];

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Bookings',
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: colors.slice(0, labels.length).map(c => c.replace('0.7', '1').replace('0.8', '1')),
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.x} bookings`
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8888a0' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f0f0f5', font: { size: 12 } }
        }
      }
    }
  });
}

/**
 * Initialize all charts with sample data (used when API is unavailable)
 */
function initWithSampleData() {
  initChartDefaults();

  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const callsData = [42, 38, 55, 47, 61, 33, 28];

  // Dashboard bar chart
  initCallsBarChart('calls-chart', dayLabels, callsData);

  // Dashboard services doughnut (reused as vertical bar on dashboard)
  const serviceLabels = ['General', 'Cosmetic', 'Implants', 'Ortho', 'Emergency'];
  const serviceData = [145, 89, 67, 52, 38];
  initServicesHorizontalBarChart('services-chart', serviceLabels, serviceData);

  // Analytics line charts
  const dateLabels = ['May 17', 'May 18', 'May 19', 'May 20', 'May 21', 'May 22', 'May 23'];
  initCallsLineChart('analytics-calls-chart', dateLabels, [35, 42, 38, 55, 47, 61, 53]);
  initBookingsLineChart('analytics-bookings-chart', dateLabels, [8, 12, 10, 15, 11, 14, 12]);

  // Analytics doughnut
  initLanguageDoughnutChart('language-chart', [
    { label: 'English', value: 78 },
    { label: 'Spanish', value: 22 }
  ]);

  // Analytics services
  initServicesHorizontalBarChart('top-services-chart',
    ['General Dentistry', 'Cosmetic', 'Dental Implants', 'Orthodontics', 'Emergency', 'Teeth Whitening'],
    [145, 89, 67, 52, 38, 31]
  );
}
