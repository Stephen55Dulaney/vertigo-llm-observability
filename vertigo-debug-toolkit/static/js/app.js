// Vertigo Debug Toolkit - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Vertigo Debug Toolkit loaded');
    
    // Check if user is authenticated by looking for authentication indicators
    const isAuthenticated = checkAuthenticationStatus();
    
    if (isAuthenticated) {
        // Initialize charts if Chart.js is available and charts don't already exist
        if (typeof Chart !== 'undefined') {
            // Only initialize if charts don't already exist (they might be initialized in the template)
            const performanceCanvas = document.getElementById('performanceChart');
            
            if (performanceCanvas && !performanceCanvas.chart) {
                initializeCharts();
            }
        }
        
        // Only load dashboard data if authenticated
        loadDashboardData();
        
        // Set up auto-refresh only for authenticated users
        setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    } else {
        console.log('User not authenticated - skipping dashboard data loading');
    }
});

function checkAuthenticationStatus() {
    // Check for authentication indicators in the DOM
    const userMenu = document.querySelector('.navbar-nav .dropdown-toggle');
    const loginForm = document.querySelector('input[name="email"]') || 
                      document.querySelector('input[name="password"]') ||
                      document.querySelector('form[method="POST"]') && document.querySelector('input[type="email"]');
    const authNavigation = document.querySelector('.navbar-nav');
    
    // Primary check: If login form is present, user is not authenticated
    if (loginForm) {
        console.log('Login form detected - user not authenticated');
        return false;
    }
    
    // Secondary check: If user dropdown menu is present, user is authenticated
    if (userMenu && userMenu.textContent.trim() !== '') {
        console.log('User menu detected - user authenticated');
        return true;
    }
    
    // Tertiary check: Look for authenticated navigation structure
    if (authNavigation && authNavigation.querySelector('a[href*="dashboard"]')) {
        console.log('Dashboard navigation detected - user likely authenticated');
        return true;
    }
    
    // Check current URL - if we're on login page, definitely not authenticated
    if (window.location.pathname.includes('/auth/login') || 
        window.location.pathname === '/' && document.title.includes('Welcome')) {
        console.log('On login/welcome page - user not authenticated');
        return false;
    }
    
    // Final check: If we're on dashboard pages, assume authenticated
    if (window.location.pathname.includes('/dashboard') || 
        window.location.pathname.includes('/prompts') ||
        window.location.pathname.includes('/performance')) {
        console.log('On authenticated page - user likely authenticated');
        return true;
    }
    
    // Default to not authenticated for safety
    console.log('No clear authentication indicators - defaulting to not authenticated');
    return false;
}

function initializeCharts() {
    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx && !performanceCtx.chart) {
        const chart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Latency (ms)',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        // Store chart reference on canvas
        performanceCtx.chart = chart;
    }
    
    // Cost Chart
    const costCtx = document.getElementById('costChart');
    if (costCtx && !costCtx.chart) {
        const chart = new Chart(costCtx, {
            type: 'doughnut',
            data: {
                labels: ['Gemini API', 'Other Costs'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: ['#28a745', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        // Store chart reference on canvas
        costCtx.chart = chart;
    }
}

function loadDashboardData() {
    // Load metrics
    fetch('/dashboard/api/metrics?days=7')
        .then(response => {
            if (response.status === 401 || response.status === 302) {
                console.log('User not authenticated - redirecting to login');
                window.location.href = '/auth/login';
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Expected JSON response but got:', contentType);
                throw new Error('Invalid response format');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                updateMetrics(data);
            }
        })
        .catch(error => {
            console.error('Error loading metrics:', error);
        });
    
    // Load recent activity
    fetch('/dashboard/api/recent-activity')
        .then(response => {
            if (response.status === 401 || response.status === 302) {
                console.log('User not authenticated - redirecting to login');
                window.location.href = '/auth/login';
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Expected JSON response but got:', contentType);
                throw new Error('Invalid response format');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                updateRecentActivity(data);
            }
        })
        .catch(error => {
            console.error('Error loading recent activity:', error);
        });
    
    // Check Vertigo status
    fetch('/dashboard/api/vertigo-status')
        .then(response => {
            if (response.status === 401 || response.status === 302) {
                console.log('User not authenticated - redirecting to login');
                window.location.href = '/auth/login';
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Expected JSON response but got:', contentType);
                throw new Error('Invalid response format');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                updateVertigoStatus(data);
            }
        })
        .catch(error => {
            console.error('Error checking Vertigo status:', error);
        });
}

function updateMetrics(data) {
    // Update metric cards
    const metricElements = {
        'total-traces': data.total_traces || 0,
        'success-rate': (data.success_rate || 0) + '%',
        'avg-latency': (data.avg_latency || 0) + 'ms',
        'total-cost': '$' + (data.total_cost || 0).toFixed(4)
    };
    
    Object.keys(metricElements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = metricElements[id];
        }
    });
}

function updateRecentActivity(data) {
    const tracesContainer = document.getElementById('recent-traces');
    if (!tracesContainer || !data.traces) return;
    
    if (data.traces.length === 0) {
        tracesContainer.innerHTML = '<p class="text-muted">No recent activity</p>';
        return;
    }
    
    const tracesHtml = data.traces.map(trace => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
                <span class="status-indicator status-${trace.status}"></span>
                <strong>${trace.name}</strong>
                <small class="text-muted">${trace.operation || 'Unknown'}</small>
            </div>
            <div class="text-end">
                <small class="text-muted">${formatDuration(trace.duration_ms)}</small><br>
                <small class="text-muted">${formatTime(trace.start_time)}</small>
            </div>
        </div>
    `).join('');
    
    tracesContainer.innerHTML = tracesHtml;
}

function updateVertigoStatus(data) {
    const statusElement = document.getElementById('vertigo-status');
    if (statusElement) {
        if (data.status === 'success') {
            statusElement.textContent = '✅ Connected';
            statusElement.className = 'text-success';
        } else {
            statusElement.textContent = '❌ Error';
            statusElement.className = 'text-danger';
        }
    }
}

function formatDuration(ms) {
    if (!ms) return 'N/A';
    if (ms < 1000) return ms + 'ms';
    return (ms / 1000).toFixed(2) + 's';
}

function formatTime(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Utility functions
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
    }
}

// Track active alerts to prevent duplication
const activeAlerts = new Set();

function showAlert(message, type = 'info', replace = false) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    // Generate unique key for this alert
    const alertKey = `${type}:${message}`;
    
    // Check for duplicate
    if (activeAlerts.has(alertKey) && !replace) {
        return; // Don't show duplicate alert
    }
    
    // Clear existing alerts if replace is true
    if (replace) {
        alertContainer.innerHTML = '';
        activeAlerts.clear();
    }
    
    activeAlerts.add(alertKey);
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" data-alert-key="${alertKey}">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    if (replace) {
        alertContainer.innerHTML = alertHtml;
    } else {
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
    }
    
    // Remove from tracking when alert is dismissed
    const alertElement = alertContainer.lastElementChild;
    alertElement.addEventListener('closed.bs.alert', function() {
        const key = this.getAttribute('data-alert-key');
        activeAlerts.delete(key);
    });
}

function clearAlerts() {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.innerHTML = '';
        activeAlerts.clear();
    }
}

// Export for global access
window.VertigoDebug = {
    loadDashboardData,
    showAlert,
    clearAlerts,
    formatDuration,
    formatTime
}; 