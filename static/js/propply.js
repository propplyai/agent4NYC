/**
 * Propply AI - Main JavaScript Module
 * Handles all interactive functionality for the application
 */

// Global state management
const PropplyApp = {
    state: {
        isLoading: false,
        currentUser: null,
        dashboardData: null,
        theme: localStorage.getItem('theme') || 'auto'
    },
    
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.checkAuthStatus();
        this.initializeTheme();
    },
    
    // Setup global event listeners
    setupEventListeners() {
        // Handle mobile menu toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('.mobile-menu-toggle')) {
                this.toggleMobileMenu();
            }
        });
        
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });
        
        // Handle theme toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('.theme-toggle') || e.target.closest('.theme-toggle')) {
                this.toggleTheme();
            }
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
    },
    
    // Initialize Bootstrap tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // Check authentication status
    checkAuthStatus() {
        // Mock authentication check
        this.state.currentUser = {
            name: 'Property Manager',
            role: 'Premium Account',
            avatar: null
        };
    },
    
    // Handle keyboard shortcuts
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.openGlobalSearch();
        }
        
        // Escape key to close modals
        if (e.key === 'Escape') {
            this.closeAllModals();
        }
    },
    
    // Handle window resize
    handleWindowResize() {
        // Adjust charts and other responsive elements
        if (window.innerWidth < 768) {
            this.enableMobileMode();
        } else {
            this.disableMobileMode();
        }
    },
    
    // Mobile menu toggle
    toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('show');
    },
    
    // Enable mobile mode
    enableMobileMode() {
        document.body.classList.add('mobile-mode');
    },
    
    // Disable mobile mode
    disableMobileMode() {
        document.body.classList.remove('mobile-mode');
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.remove('show');
    },
    
    // Open global search
    openGlobalSearch() {
        const searchModal = document.getElementById('globalSearchModal');
        if (searchModal) {
            const modal = new bootstrap.Modal(searchModal);
            modal.show();
        }
    },
    
    // Close all modals
    closeAllModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    },
    
    // Handle AJAX form submissions
    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.pathname;
        const method = form.method || 'POST';
        
        try {
            this.showLoading(true);
            
            const response = await fetch(url, {
                method: method,
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccess(result.message || 'Operation completed successfully');
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                this.showError(result.error || 'Operation failed');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showError('Network error occurred');
        } finally {
            this.showLoading(false);
        }
    },
    
    // Theme management
    initializeTheme() {
        this.applyTheme(this.state.theme);
    },
    
    applyTheme(theme) {
        const html = document.documentElement;
        
        if (theme === 'dark') {
            html.setAttribute('data-theme', 'dark');
        } else if (theme === 'light') {
            html.removeAttribute('data-theme');
        } else {
            // Auto mode - follow system preference
            html.removeAttribute('data-theme');
        }
        
        this.state.theme = theme;
        localStorage.setItem('theme', theme);
        this.updateThemeToggleIcon();
    },
    
    toggleTheme() {
        let newTheme;
        switch (this.state.theme) {
            case 'light':
                newTheme = 'dark';
                break;
            case 'dark':
                newTheme = 'auto';
                break;
            default:
                newTheme = 'light';
                break;
        }
        this.applyTheme(newTheme);
    },
    
    updateThemeToggleIcon() {
        const toggleButton = document.querySelector('.theme-toggle');
        if (!toggleButton) return;
        
        const icon = toggleButton.querySelector('i');
        if (!icon) return;
        
        icon.className = '';
        switch (this.state.theme) {
            case 'light':
                icon.className = 'fas fa-sun';
                break;
            case 'dark':
                icon.className = 'fas fa-moon';
                break;
            default:
                icon.className = 'fas fa-adjust';
                break;
        }
    }
};

// Utility Functions
function showLoading(show = true) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
    PropplyApp.state.isLoading = show;
}

function showSuccess(message) {
    showToast('success', message);
}

function showError(message) {
    showToast('error', message);
}

function showInfo(message) {
    showToast('info', message);
}

function showWarning(message) {
    showToast('warning', message);
}

function showToast(type, message) {
    const toastId = type + 'Toast';
    const toastElement = document.getElementById(toastId);
    
    if (!toastElement) {
        // Create toast dynamically if it doesn't exist
        createToast(type, message);
        return;
    }
    
    const toastBody = toastElement.querySelector('.toast-body');
    if (toastBody) {
        toastBody.textContent = message;
    }
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 5000 : 3000
    });
    
    toast.show();
}

function createToast(type, message) {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;
    
    const toastColors = {
        success: 'bg-success',
        error: 'bg-danger',
        warning: 'bg-warning',
        info: 'bg-info'
    };
    
    const toastIcons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    const toastElement = document.createElement('div');
    toastElement.className = 'toast';
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="toast-header ${toastColors[type]}">
            <i class="${toastIcons[type]} me-2" style="color: white;"></i>
            <strong class="me-auto" style="color: white;">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" style="filter: brightness(0) invert(1);"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 5000 : 3000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// API Helper Functions
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(endpoint, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

async function searchProperties(address, zipCode = null) {
    return await apiRequest('/api/search', {
        method: 'POST',
        body: JSON.stringify({
            address: address,
            zip_code: zipCode
        })
    });
}

async function generateComplianceReport(bin, borough, block, lot) {
    return await apiRequest('/api/compliance', {
        method: 'POST',
        body: JSON.stringify({
            bin: bin,
            borough: borough,
            block: block,
            lot: lot
        })
    });
}

async function generateAIAnalysis(complianceData, propertyInfo) {
    return await apiRequest('/api/ai-analysis', {
        method: 'POST',
        body: JSON.stringify({
            compliance_data: complianceData,
            property_info: propertyInfo
        })
    });
}

async function getDashboardData() {
    return await apiRequest('/api/dashboard-data');
}

// Chart Utilities
function createLineChart(canvas, data, options = {}) {
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        },
        elements: {
            line: {
                tension: 0.4
            },
            point: {
                radius: 4,
                hoverRadius: 6
            }
        }
    };
    
    const config = {
        type: 'line',
        data: data,
        options: { ...defaultOptions, ...options }
    };
    
    return new Chart(ctx, config);
}

function createBarChart(canvas, data, options = {}) {
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        }
    };
    
    const config = {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    };
    
    return new Chart(ctx, config);
}

function createDoughnutChart(canvas, data, options = {}) {
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        },
        cutout: '60%'
    };
    
    const config = {
        type: 'doughnut',
        data: data,
        options: { ...defaultOptions, ...options }
    };
    
    return new Chart(ctx, config);
}

// Data Formatting Utilities
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
}

function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
}

function formatRelativeTime(date) {
    const now = new Date();
    const targetDate = new Date(date);
    const diffInSeconds = Math.floor((now - targetDate) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    
    return formatDate(date);
}

function formatPercentage(value, decimals = 1) {
    return `${value.toFixed(decimals)}%`;
}

// Validation Utilities
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
    return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

function validateAddress(address) {
    return address && address.trim().length > 5;
}

function validateZipCode(zipCode) {
    const zipRegex = /^\d{5}(-\d{4})?$/;
    return zipRegex.test(zipCode);
}

// Local Storage Utilities
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to storage:', error);
        return false;
    }
}

function loadFromStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Failed to load from storage:', error);
        return null;
    }
}

function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from storage:', error);
        return false;
    }
}

// Animation Utilities
function fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';
    
    let start = null;
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const opacity = Math.min(progress / duration, 1);
        
        element.style.opacity = opacity;
        
        if (progress < duration) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    let start = null;
    const initialOpacity = parseFloat(getComputedStyle(element).opacity);
    
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const opacity = initialOpacity * (1 - Math.min(progress / duration, 1));
        
        element.style.opacity = opacity;
        
        if (progress < duration) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}

function slideDown(element, duration = 300) {
    element.style.height = '0';
    element.style.overflow = 'hidden';
    element.style.display = 'block';
    
    const targetHeight = element.scrollHeight;
    let start = null;
    
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const height = (targetHeight * Math.min(progress / duration, 1));
        
        element.style.height = height + 'px';
        
        if (progress < duration) {
            requestAnimationFrame(animate);
        } else {
            element.style.height = 'auto';
            element.style.overflow = 'visible';
        }
    }
    
    requestAnimationFrame(animate);
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    PropplyApp.init();
});

// Export global functions for use in templates
window.PropplyApp = PropplyApp;
window.showLoading = showLoading;
window.showSuccess = showSuccess;
window.showError = showError;
window.showInfo = showInfo;
window.showWarning = showWarning;
window.apiRequest = apiRequest;
window.searchProperties = searchProperties;
window.generateComplianceReport = generateComplianceReport;
window.generateAIAnalysis = generateAIAnalysis;
window.getDashboardData = getDashboardData;
