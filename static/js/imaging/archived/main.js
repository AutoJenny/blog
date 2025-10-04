// imaging-main.js - Main JavaScript file for BlogForge Imaging Module
// This file provides common functionality for imaging pages

console.log('BlogForge imaging-main.js loaded');

// Imaging-specific utility functions
function imagingShowNotification(message, type = 'info') {
    // Simple notification system for imaging
    const notification = document.createElement('div');
    notification.className = `imaging-notification imaging-notification-${type}`;
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

// Initialize imaging-specific functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('BlogForge imaging-main.js initialized');
    
    // Add any imaging-specific initialization code here
    imagingInitializeCommonFeatures();
});

function imagingInitializeCommonFeatures() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize any other imaging-specific features
    imagingInitializeDarkMode();
    imagingInitializeImageHandlers();
}

function imagingInitializeDarkMode() {
    // Ensure dark mode is properly applied for imaging
    if (!document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.add('dark');
    }
}

function imagingInitializeImageHandlers() {
    // Initialize image-specific event handlers
    console.log('[Imaging Main] Initializing image handlers');
    
    // Handle image loading states
    document.addEventListener('load', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.classList.add('loaded');
        }
    }, true);
    
    // Handle image error states
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.classList.add('error');
            console.error('[Imaging Main] Image failed to load:', e.target.src);
        }
    }, true);
}

// Imaging-specific utility functions
function imagingFormatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function imagingValidateImageDimensions(width, height) {
    // Validate image dimensions for imaging workflow
    const minWidth = 256;
    const minHeight = 256;
    const maxWidth = 4096;
    const maxHeight = 4096;
    
    return {
        valid: width >= minWidth && width <= maxWidth && height >= minHeight && height <= maxHeight,
        minWidth,
        minHeight,
        maxWidth,
        maxHeight
    };
}

function imagingGetImageAspectRatio(width, height) {
    const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
    const divisor = gcd(width, height);
    return `${width / divisor}:${height / divisor}`;
}

// Export functions for use in other imaging scripts
window.ImagingForge = {
    showNotification: imagingShowNotification,
    initializeCommonFeatures: imagingInitializeCommonFeatures,
    formatFileSize: imagingFormatFileSize,
    validateImageDimensions: imagingValidateImageDimensions,
    getImageAspectRatio: imagingGetImageAspectRatio
};
