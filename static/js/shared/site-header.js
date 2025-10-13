// Site Header (Shared) - Self-contained scripts

document.addEventListener('DOMContentLoaded', function() {
    // Navigation dropdown focus/blur behavior
    document.querySelectorAll('.nav-group').forEach(group => {
        group.addEventListener('focusin', () => {
            const dd = group.querySelector('.nav-dropdown');
            if (dd) dd.classList.remove('hidden');
        });
        group.addEventListener('focusout', () => {
            setTimeout(() => {
                const dd = group.querySelector('.nav-dropdown');
                if (dd) dd.classList.add('hidden');
            }, 100);
        });
    });

    // Initialize alert system
    initializeAlertSystem();

    // Expose simple API for automation
    window.headerMessages = {
        addMessage(messageData) {
            const alert = {
                id: Date.now() + Math.random(),
                title: messageData.title || 'Automation Alert',
                message: messageData.message,
                alert_type: messageData.type || 'warning',
                severity: messageData.type || 'warning',
                created_at: new Date().toISOString(),
                is_read: false,
                action_text: 'View Details',
                action_url: messageData.action_url || '/launchpad/one-click-blog'
            };
            alerts.unshift(alert);
            updateAlertBadge();
            if (alertDropdownOpen) renderAlerts();
        },
        getUnreadCount() { return alerts.filter(a => !a.is_read).length; },
        markAllRead() { markAllAlertsRead(); }
    };
});

// Alert System
let alerts = [];
let alertDropdownOpen = false;

function initializeAlertSystem() {
    loadAlerts();
    setInterval(loadAlerts, 30000);
}

async function loadAlerts() {
    // TODO: hook real API; mock for now
    alerts = [
        { id: 1, alert_type: 'stuck_post', severity: 'warning', post_id: 76, title: 'Post #76 Stuck at Image Generation', message: 'Failed 3 times - needs manual attention', action_url: '/launchpad/one-click-blog?post=76', action_text: 'View Post', created_at: new Date().toISOString(), is_read: false }
    ];
    updateAlertBadge();
    if (alertDropdownOpen) updateAlertDropdown();
}

function updateAlertBadge() {
    const badge = document.getElementById('alert-badge');
    if (!badge) return;
    const unreadCount = alerts.filter(a => !a.is_read).length;
    badge.textContent = unreadCount;
    badge.style.display = unreadCount > 0 ? 'flex' : 'none';
}

function toggleAlertDropdown() {
    const dropdown = document.getElementById('alert-dropdown');
    if (!dropdown) return;
    alertDropdownOpen = !alertDropdownOpen;
    if (alertDropdownOpen) { dropdown.classList.remove('hidden'); updateAlertDropdown(); }
    else { dropdown.classList.add('hidden'); }
}

function updateAlertDropdown() {
    const alertList = document.getElementById('alert-list');
    if (!alertList) return;
    if (alerts.length === 0) {
        alertList.innerHTML = `<div class="no-alerts"><i class="fas fa-bell-slash"></i><p>No alerts</p></div>`;
        return;
    }
    alertList.innerHTML = alerts.map(createAlertItem).join('');
}

function createAlertItem(alert) {
    const timeAgo = 'just now';
    const icon = getAlertIcon(alert.alert_type);
    return `<div class="alert-item ${alert.severity} ${alert.is_read ? '' : 'unread'}" onclick="handleAlertClick(${alert.id})">
        <div class="alert-content">
            <i class="fas ${icon} alert-icon ${alert.severity}"></i>
            <div class="alert-details">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${timeAgo}</div>
                <div class="alert-actions">
                    <button class="alert-action-btn primary" onclick="event.stopPropagation(); handleAlertAction(${alert.id}, '${alert.action_url}')">${alert.action_text}</button>
                    <button class="alert-action-btn" onclick="event.stopPropagation(); dismissAlert(${alert.id})">Dismiss</button>
                </div>
            </div>
        </div>
    </div>`;
}

function getAlertIcon(alertType) {
    const icons = { stuck_post: 'fa-exclamation-triangle', ready_publish: 'fa-clock', missing_schedule: 'fa-calendar-times', low_queue: 'fa-chart-line', manual_review: 'fa-eye', completion: 'fa-check-circle' };
    return icons[alertType] || 'fa-info-circle';
}

function handleAlertClick(alertId) {
    const a = alerts.find(x => x.id === alertId);
    if (a) { a.is_read = true; updateAlertBadge(); updateAlertDropdown(); }
}

function handleAlertAction(alertId, actionUrl) {
    const a = alerts.find(x => x.id === alertId);
    if (a) { a.is_read = true; updateAlertBadge(); updateAlertDropdown(); window.location.href = actionUrl; }
}

function dismissAlert(alertId) {
    alerts = alerts.filter(a => a.id !== alertId);
    updateAlertBadge();
    updateAlertDropdown();
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const alertContainer = document.getElementById('alert-container');
    const dropdown = document.getElementById('alert-dropdown');
    if (alertContainer && dropdown && !alertContainer.contains(event.target)) {
        dropdown.classList.add('hidden');
        alertDropdownOpen = false;
    }
});


