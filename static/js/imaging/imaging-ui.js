// Imaging UI JavaScript - Streamlined UI Interactions
// Consolidated UI functionality (50 lines)

console.log('Imaging UI loaded');

// UI initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Imaging UI] Initializing');
    
    setupAccordions();
    setupGenerateButton();
    setupRefreshButton();
});

// Accordion functionality
function setupAccordions() {
    // Model selection accordion
    const modelHeader = document.querySelector('.model-selection-panel .panel-header');
    const modelContent = document.getElementById('model-accordion-content');
    const modelIcon = document.getElementById('model-accordion-icon');
    
    if (modelHeader && modelContent) {
        modelHeader.addEventListener('click', function() {
            const isOpen = modelContent.style.display !== 'none';
            modelContent.style.display = isOpen ? 'none' : 'block';
            modelIcon.className = isOpen ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
            localStorage.setItem('imaging-model-accordion', isOpen ? 'closed' : 'open');
        });
        
        // Restore state
        const savedState = localStorage.getItem('imaging-model-accordion');
        if (savedState === 'open') {
            modelContent.style.display = 'block';
            modelIcon.className = 'fas fa-chevron-up';
        }
    }
}

// Generate button
function setupGenerateButton() {
    const generateBtn = document.getElementById('generate-image-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateImage);
    }
}

// Refresh button
function setupRefreshButton() {
    const refreshBtn = document.getElementById('refresh-sections');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            if (typeof loadSections === 'function') {
                loadSections();
            }
        });
    }
}

// Simple notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 10px 20px;
        background: #23273a; color: #e0e0e0; border: 1px solid #31364a;
        border-radius: 4px; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Make functions globally available
window.showNotification = showNotification;
