/* ============================================
   Renia AI — Chart Module (Chart.js)
   Stark Monochrome Black & White Aesthetic
   ============================================ */

// Chart.js global defaults for LIGHT monochrome theme
function initChartDefaults() {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded');
    return;
  }

  Chart.defaults.color = '#555555';
  Chart.defaults.borderColor = 'rgba(0, 0, 0, 0.08)';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.95)';
  Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
  Chart.defaults.plugins.tooltip.bodyColor = '#e5e5e5';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.displayColors = false;
  Chart.defaults.scale.grid = Chart.defaults.scale.grid || {};
  Chart.defaults.scale.grid.color = 'rgba(0, 0, 0, 0.05)';
}

/**
 * Initialize a bar chart for calls data
 */
function initCallsBarChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const ctx = canvas.getContext('2d');

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Calls',
        data: data,
        backgroundColor: '#000000',
        borderColor: '#000000',
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
        maxBarThickness: 32
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
          ticks: { color: '#555555' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: {
            color: '#555555',
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

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Calls',
        data: data,
        borderColor: '#000000',
        backgroundColor: 'rgba(0, 0, 0, 0.02)',
        borderWidth: 2,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#000000',
        pointBorderColor: '#ffffff',
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
          ticks: { color: '#555555' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { color: '#555555' }
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

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Bookings',
        data: data,
        borderColor: '#676767',
        backgroundColor: 'rgba(0, 0, 0, 0.01)',
        borderWidth: 2,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#676767',
        pointBorderColor: '#ffffff',
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
          ticks: { color: '#555555' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { color: '#555555' }
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

  const colors = [
    '#000000',
    '#676767',
    '#A3A3A3',
    '#E5E5E5'
  ];

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 8,
            color: '#555555'
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
    '#000000',
    '#2D2D2D',
    '#555555',
    '#676767',
    '#808080',
    '#A3A3A3',
    '#CCCCCC',
    '#E5E5E5'
  ];

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Bookings',
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#ffffff',
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
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { color: '#555555' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#2D2D2D', font: { size: 12 } }
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
