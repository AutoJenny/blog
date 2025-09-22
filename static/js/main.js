// main.js - Main JavaScript file for BlogForge Unified Application
// This file provides common functionality across all pages

console.log('BlogForge main.js loaded');

// Common utility functions
function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        background: #23273a;
        color: #e0e0e0;
        border: 1px solid #31364a;
        border-radius: 4px;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize common functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('BlogForge main.js initialized');
    
    // Add any common initialization code here
    initializeCommonFeatures();
});

function initializeCommonFeatures() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize any other common features
    initializeDarkMode();
}

function initializeDarkMode() {
    // Ensure dark mode is properly applied
    if (!document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.add('dark');
    }
}

// Export functions for use in other scripts
window.BlogForge = {
    showNotification: showNotification,
    initializeCommonFeatures: initializeCommonFeatures
};
