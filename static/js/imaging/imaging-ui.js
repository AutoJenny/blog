// Imaging UI JavaScript - Streamlined UI Interactions
// Consolidated UI functionality (50 lines)

console.log('Imaging UI loaded');

// UI initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Imaging UI] Initializing');
    
    setupAccordions();
    // setupGenerateButton(); // Handled by ImageGenerationHandler
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
            sessionStorage.setItem('imaging-model-accordion', isOpen ? 'closed' : 'open');
        });
        
        // Restore state (default to closed)
        const savedState = sessionStorage.getItem('imaging-model-accordion');
        if (savedState === 'open') {
            modelContent.style.display = 'block';
            modelIcon.className = 'fas fa-chevron-up';
        } else {
            modelContent.style.display = 'none';
            modelIcon.className = 'fas fa-chevron-down';
        }
    }
    
    // Prompt construction accordion
    const promptContent = document.getElementById('prompt-accordion-content');
    const promptIcon = document.getElementById('prompt-accordion-icon');
    
    if (promptContent && promptIcon) {
        // Restore state (default to open)
        const savedState = sessionStorage.getItem('imaging-prompt-accordion');
        if (savedState === 'closed') {
            promptContent.style.display = 'none';
            promptIcon.className = 'fas fa-chevron-down';
        } else {
            promptContent.style.display = 'block';
            promptIcon.className = 'fas fa-chevron-up';
        }
    }
}

// Generate button - handled by ImageGenerationHandler
// function setupGenerateButton() {
//     const generateBtn = document.getElementById('generate-image-btn');
//     if (generateBtn) {
//         generateBtn.addEventListener('click', generateImage);
//     }
// }

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

// Prompt construction accordion
function togglePromptConstructionAccordion() {
    const content = document.getElementById('prompt-accordion-content');
    const icon = document.getElementById('prompt-accordion-icon');
    
    if (content && icon) {
        const isOpen = content.style.display !== 'none';
        content.style.display = isOpen ? 'none' : 'block';
        icon.className = isOpen ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
        sessionStorage.setItem('imaging-prompt-accordion', isOpen ? 'closed' : 'open');
    }
}

// Make functions globally available
window.showNotification = showNotification;
window.togglePromptConstructionAccordion = togglePromptConstructionAccordion;
