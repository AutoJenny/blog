/**
 * Imaging Workspace - Main Coordination Script
 * Handles initialization and coordination between all imaging panels
 */

// Imaging-specific utility functions
window.ImagingUtils = {
    // Initialize imaging workspace
    init: function() {
        console.log('Imaging workspace initialized');
        this.setupEventListeners();
    },
    
    // Setup global event listeners
    setupEventListeners: function() {
        // Add any global imaging event listeners here
    },
    
    // Imaging-specific state management
    state: {
        currentPost: null,
        currentSection: null,
        selectedModel: 'sdxl-lora'
    },
    
    // Update imaging state
    updateState: function(key, value) {
        this.state[key] = value;
        localStorage.setItem(`imaging-${key}`, JSON.stringify(value));
    },
    
    // Get imaging state
    getState: function(key) {
        const stored = localStorage.getItem(`imaging-${key}`);
        return stored ? JSON.parse(stored) : this.state[key];
    }
};

// Imaging-specific accordion functions
function toggleImagingInputDetailsAccordion() {
    const content = document.getElementById('imaging-input-details-accordion-content');
    const icon = document.getElementById('imaging-input-details-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('imaging-input-details-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('imaging-input-details-accordion-state', 'closed');
    }
}

function toggleModelSelectionAccordion() {
    const content = document.getElementById('model-selection-accordion-content');
    const icon = document.getElementById('model-selection-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('model-selection-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('model-selection-accordion-state', 'closed');
    }
}

// Note: Prompt Construction accordion is managed by its own self-contained module
// to avoid ID/key mismatches and duplicate state handling.

function toggleDebuggingAccordion() {
    const content = document.getElementById('debugging-accordion-content');
    const icon = document.getElementById('debugging-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('debugging-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('debugging-accordion-state', 'closed');
    }
}

// Restore accordion states on page load
function restoreImagingAccordionStates() {
    // Restore Input Details accordion state
    const inputDetailsState = localStorage.getItem('imaging-input-details-accordion-state');
    if (inputDetailsState === 'open') {
        const content = document.getElementById('imaging-input-details-accordion-content');
        const icon = document.getElementById('imaging-input-details-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Restore Model Selection accordion state
    const modelState = localStorage.getItem('model-selection-accordion-state');
    if (modelState === 'open') {
        const content = document.getElementById('model-selection-accordion-content');
        const icon = document.getElementById('model-selection-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Prompt Construction accordion state is restored by its own module
    
    // Restore Debugging accordion state
    const debuggingState = localStorage.getItem('debugging-accordion-state');
    if (debuggingState === 'open') {
        const content = document.getElementById('debugging-accordion-content');
        const icon = document.getElementById('debugging-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Imaging workspace loaded, initializing panels');
    
    // Restore accordion states
    restoreImagingAccordionStates();
    
    // Initialize imaging workspace
    window.ImagingUtils.init();
    
    // Panel modules self-initialize on DOMContentLoaded via their own JS files
    // No need to explicitly instantiate them here to avoid duplicate variable errors
    
    // Initialize Imaging Sections Panel with simple callbacks
    if (typeof ImagingSectionsPanel !== 'undefined') {
        const sectionsPanel = new ImagingSectionsPanel({
            postId: window.postId,
            onSectionSelect: async (data) => {
                console.log('Section selected:', data);
                window.currentSectionId = data.sectionId;
                
                // Dispatch sectionSelected event so all panels can respond
                const event = new CustomEvent('sectionSelected', {
                    detail: {
                        sectionId: data.sectionId,
                        section: data.section,
                        postId: data.postId
                    }
                });
                document.dispatchEvent(event);
                
                // Also dispatch legacy event name for compatibility
                const legacyEvent = new CustomEvent('section-selected', {
                    detail: {
                        sectionId: data.sectionId,
                        section: data.section,
                        postId: data.postId
                    }
                });
                document.dispatchEvent(legacyEvent);
                
                // Update output panel if it exists
                if (window.imagingOutputPanel) {
                    window.imagingOutputPanel.loadSectionImages(data.sectionId);
                    window.imagingOutputPanel.updateSectionTitle(data.sectionTitle || `Section ${data.sectionId}`);
                }
            },
            onBatchStart: (selectedIds) => {
                console.log('[Imaging Workspace] Batch generation started for sections:', selectedIds);
            },
            onBatchProgress: (progress) => {
                console.log('[Imaging Workspace] Batch progress:', progress);
                // Show progress in console and UI
                if (progress.status === 'generating') {
                    const imageTypeText = progress.imageType ? ` (${progress.imageType})` : '';
                    console.log(`Generating image ${progress.current}/${progress.total}: ${progress.sectionTitle}${imageTypeText}`);
                    showBatchProgress(progress);
                } else if (progress.status === 'success') {
                    const imageTypeText = progress.imageType ? ` (${progress.imageType})` : '';
                    console.log(`✓ Successfully generated image ${progress.current}/${progress.total}: ${progress.sectionTitle}${imageTypeText}`);
                    updateBatchProgress(progress);
                } else if (progress.status === 'error') {
                    const imageTypeText = progress.imageType ? ` (${progress.imageType})` : '';
                    console.error(`✗ Error generating image ${progress.current}/${progress.total}: ${progress.sectionTitle}${imageTypeText} - ${progress.error}`);
                    updateBatchProgress(progress);
                }
            },
            onBatchComplete: (result) => {
                console.log('[Imaging Workspace] Batch generation complete:', result);
                if (result.totalImages) {
                    showTransientMessage(`Batch generation complete! Generated ${result.totalImages} images across ${result.totalSections} section${result.totalSections !== 1 ? 's' : ''}.`, 5000);
                } else {
                    showTransientMessage(`Batch generation complete! Generated ${result.successCount} of ${result.totalSections} sections.`, 5000);
                }
            }
        });
        
        // Make sections panel globally available
        window.imagingSectionsPanel = sectionsPanel;
        
        console.log('Imaging Sections Panel initialized successfully');
    } else {
        console.error('ImagingSectionsPanel class not found');
    }
    
    console.log('All imaging panels initialized successfully');
});

// Transient message function
function showTransientMessage(message, duration = 3000) {
    // Remove any existing transient message
    const existing = document.getElementById('transient-message');
    if (existing) {
        existing.remove();
    }
    
    // Create new transient message
    const msg = document.createElement('div');
    msg.id = 'transient-message';
    msg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #1e293b;
        border: 1px solid #334155;
        color: #e2e8f0;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        font-size: 0.9rem;
        max-width: 400px;
    `;
    msg.textContent = message;
    document.body.appendChild(msg);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (msg.parentNode) {
            msg.parentNode.removeChild(msg);
        }
    }, duration);
}

// Batch progress UI functions
let batchProgressContainer = null;

function showBatchProgress(progress) {
    if (!batchProgressContainer) {
        // Create progress container
        batchProgressContainer = document.createElement('div');
        batchProgressContainer.id = 'batch-progress-container';
        batchProgressContainer.style.cssText = 'position:fixed;top:20px;right:20px;background:#0f172a;border:1px solid #334155;border-radius:8px;padding:1rem;min-width:300px;z-index:10000;box-shadow:0 4px 6px rgba(0,0,0,0.3);';
        document.body.appendChild(batchProgressContainer);
    }
    
    const imageTypeText = progress.imageType ? ` (${progress.imageType})` : '';
    const progressHtml = `
        <div style="color:#e2e8f0;font-weight:bold;margin-bottom:0.5rem;">Generating Images</div>
        <div style="color:#94a3b8;font-size:0.9rem;margin-bottom:0.5rem;">
            ${progress.current} / ${progress.total}: ${progress.sectionTitle || progress.sectionId}${imageTypeText}
        </div>
        <div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">
            <div style="background:#10b981;height:100%;width:${(progress.current / progress.total) * 100}%;transition:width 0.3s;"></div>
        </div>
    `;
    batchProgressContainer.innerHTML = progressHtml;
    batchProgressContainer.style.display = 'block';
}

function updateBatchProgress(progress) {
    if (!batchProgressContainer) return;
    
    const statusIcon = progress.status === 'success' ? '✓' : progress.status === 'error' ? '✗' : '';
    const statusColor = progress.status === 'success' ? '#10b981' : progress.status === 'error' ? '#ef4444' : '#94a3b8';
    const imageTypeText = progress.imageType ? ` (${progress.imageType})` : '';
    
    const progressHtml = `
        <div style="color:#e2e8f0;font-weight:bold;margin-bottom:0.5rem;">Generating Images</div>
        <div style="color:${statusColor};font-size:0.9rem;margin-bottom:0.5rem;">
            ${statusIcon} ${progress.current} / ${progress.total}: ${progress.sectionTitle || progress.sectionId}${imageTypeText}
            ${progress.error ? `<div style="color:#ef4444;font-size:0.8rem;margin-top:0.25rem;">${progress.error}</div>` : ''}
        </div>
        <div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">
            <div style="background:${progress.status === 'success' ? '#10b981' : progress.status === 'error' ? '#ef4444' : '#3b82f6'};height:100%;width:${(progress.current / progress.total) * 100}%;transition:width 0.3s;"></div>
        </div>
    `;
    batchProgressContainer.innerHTML = progressHtml;
    
    // Hide after 3 seconds if complete
    if (progress.current >= progress.total && progress.status !== 'generating') {
        setTimeout(() => {
            if (batchProgressContainer) {
                batchProgressContainer.style.display = 'none';
            }
        }, 3000);
    }
}

// Export functions for global access
window.toggleImagingInputDetailsAccordion = toggleImagingInputDetailsAccordion;
window.toggleModelSelectionAccordion = toggleModelSelectionAccordion;
// Prompt Construction toggle is exported by its own module
window.toggleDebuggingAccordion = toggleDebuggingAccordion;
