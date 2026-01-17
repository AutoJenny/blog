/**
 * Monitoring Module
 * Handles status display and control for automation monitoring
 */

(function() {
    'use strict';
    
    const STATUS_ICON = document.getElementById('monitoring-status-icon');
    const START_BTN = document.getElementById('monitoring-start-btn');
    
    if (!STATUS_ICON || !START_BTN) {
        return; // Module not present on this page
    }
    
    let statusCheckInterval = null;
    
    /**
     * Update monitoring status display
     */
    function updateStatus() {
        fetch('/monitoring/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.is_running) {
                        STATUS_ICON.className = 'fa-solid fa-circle status-running';
                        START_BTN.classList.add('hidden');
                    } else {
                        STATUS_ICON.className = 'fa-solid fa-circle status-stopped';
                        START_BTN.classList.remove('hidden');
                    }
                }
            })
            .catch(error => {
                console.error('Error checking monitoring status:', error);
            });
    }
    
    /**
     * Start monitoring
     */
    function startMonitoring() {
        START_BTN.disabled = true;
        START_BTN.textContent = 'Starting...';
        
        fetch('/monitoring/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatus();
                    setTimeout(() => {
                        START_BTN.disabled = false;
                        START_BTN.textContent = 'Start';
                    }, 2000);
                } else {
                    alert('Failed to start monitoring: ' + (data.error || 'Unknown error'));
                    START_BTN.disabled = false;
                    START_BTN.textContent = 'Start';
                }
            })
            .catch(error => {
                console.error('Error starting monitoring:', error);
                alert('Error starting monitoring: ' + error.message);
                START_BTN.disabled = false;
                START_BTN.textContent = 'Start';
            });
    }
    
    // Initialize
    updateStatus();
    
    // Check status every 30 seconds
    statusCheckInterval = setInterval(updateStatus, 30000);
    
    // Start button click handler
    START_BTN.addEventListener('click', startMonitoring);
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }
    });
})();
