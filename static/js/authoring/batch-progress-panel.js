/**
 * Batch Progress Panel - Modular Component
 * Self-contained module for managing batch operation progress display
 */

class BatchProgressPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'batch-progress-panel';
        this.postId = options.postId || window.postId;
        
        // Callbacks for external communication
        this.callbacks = {
            onBatchStart: options.onBatchStart || (() => {}),
            onBatchProgress: options.onBatchProgress || (() => {}),
            onBatchComplete: options.onBatchComplete || (() => {}),
            onBatchCancel: options.onBatchCancel || (() => {})
        };
        
        // DOM elements
        this.panel = null;
        this.progressPercent = null;
        this.progressFill = null;
        this.progressText = null;
        this.sectionResults = null;
        
        // State
        this.isVisible = false;
        this.currentBatch = null;
        this.sectionProgress = new Map();
        
        this.init();
    }

    init() {
        this.bindElements();
        this.setupEventListeners();
        this.restoreAccordionState();
    }

    bindElements() {
        this.panel = document.getElementById(this.containerId);
        this.progressPercent = document.getElementById('progress-percent');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.sectionResults = document.getElementById('section-results');
    }

    setupEventListeners() {
        // Accordion functionality is handled by the global toggleBatchProgressAccordion function
    }

    show() {
        if (this.panel) {
            this.panel.style.display = 'block';
            this.isVisible = true;
        }
    }

    hide() {
        if (this.panel) {
            this.panel.style.display = 'none';
            this.isVisible = false;
        }
    }

    startBatch(sectionIds, operation = 'generate') {
        this.currentBatch = {
            sectionIds: sectionIds,
            operation: operation,
            totalSections: sectionIds.length,
            completedSections: 0,
            startTime: Date.now()
        };
        
        this.sectionProgress.clear();
        this.show();
        this.updateProgress(0, 'Starting batch operation...');
        this.clearSectionResults();
        
        // Initialize section progress tracking
        sectionIds.forEach(sectionId => {
            this.sectionProgress.set(sectionId, {
                status: 'pending',
                progress: 0,
                startTime: null,
                endTime: null,
                error: null
            });
        });
        
        this.renderSectionResults();
        this.callbacks.onBatchStart(this.currentBatch);
        
        console.log(`[Batch Progress Panel] Started batch operation: ${operation} for ${sectionIds.length} sections`);
    }

    updateSectionProgress(sectionId, progress, status = 'processing') {
        if (!this.sectionProgress.has(sectionId)) {
            return;
        }
        
        const sectionData = this.sectionProgress.get(sectionId);
        sectionData.progress = Math.max(0, Math.min(100, progress));
        sectionData.status = status;
        
        if (status === 'processing' && !sectionData.startTime) {
            sectionData.startTime = Date.now();
        }
        
        if (status === 'completed' || status === 'error') {
            sectionData.endTime = Date.now();
            this.currentBatch.completedSections++;
        }
        
        this.sectionProgress.set(sectionId, sectionData);
        this.renderSectionResults();
        this.updateOverallProgress();
        
        this.callbacks.onBatchProgress({
            sectionId: sectionId,
            progress: progress,
            status: status,
            batch: this.currentBatch
        });
    }

    updateOverallProgress() {
        if (!this.currentBatch) return;
        
        const totalProgress = Array.from(this.sectionProgress.values())
            .reduce((sum, section) => sum + section.progress, 0);
        
        const averageProgress = totalProgress / this.currentBatch.totalSections;
        const roundedProgress = Math.round(averageProgress);
        
        this.updateProgress(roundedProgress, this.getProgressText());
        
        // Check if batch is complete
        if (this.currentBatch.completedSections >= this.currentBatch.totalSections) {
            this.completeBatch();
        }
    }

    updateProgress(percent, text) {
        if (this.progressPercent) {
            this.progressPercent.textContent = `${percent}%`;
        }
        
        if (this.progressFill) {
            this.progressFill.style.width = `${percent}%`;
        }
        
        if (this.progressText) {
            this.progressText.textContent = text;
        }
    }

    getProgressText() {
        if (!this.currentBatch) return 'Ready to generate';
        
        const completed = this.currentBatch.completedSections;
        const total = this.currentBatch.totalSections;
        
        if (completed === 0) {
            return 'Starting batch operation...';
        } else if (completed < total) {
            return `Processing ${completed} of ${total} sections...`;
        } else {
            return 'Batch operation completed!';
        }
    }

    completeBatch() {
        if (!this.currentBatch) return;
        
        const duration = Date.now() - this.currentBatch.startTime;
        const durationText = this.formatDuration(duration);
        
        this.updateProgress(100, `Completed in ${durationText}`);
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hide();
        }, 3000);
        
        this.callbacks.onBatchComplete({
            batch: this.currentBatch,
            duration: duration,
            results: Array.from(this.sectionProgress.entries())
        });
        
        console.log(`[Batch Progress Panel] Batch completed in ${durationText}`);
    }

    cancelBatch() {
        if (!this.currentBatch) return;
        
        this.updateProgress(0, 'Batch operation cancelled');
        this.hide();
        
        this.callbacks.onBatchCancel(this.currentBatch);
        this.currentBatch = null;
        
        console.log('[Batch Progress Panel] Batch cancelled');
    }

    clearSectionResults() {
        if (this.sectionResults) {
            this.sectionResults.innerHTML = '';
        }
    }

    renderSectionResults() {
        if (!this.sectionResults || !this.currentBatch) return;
        
        this.sectionResults.innerHTML = '';
        
        this.currentBatch.sectionIds.forEach(sectionId => {
            const sectionData = this.sectionProgress.get(sectionId);
            if (sectionData) {
                const sectionElement = this.createSectionResultElement(sectionId, sectionData);
                this.sectionResults.appendChild(sectionElement);
            }
        });
    }

    createSectionResultElement(sectionId, sectionData) {
        const div = document.createElement('div');
        div.className = 'section-result';
        
        const statusIcon = this.getStatusIcon(sectionData.status);
        const statusText = this.getStatusText(sectionData.status);
        const duration = sectionData.endTime ? 
            this.formatDuration(sectionData.endTime - sectionData.startTime) : '';
        
        // Try to get section title from sections panel or sections data
        let sectionTitle = `Section ${sectionId}`;
        try {
            // Check if sections panel has section data
            if (window.sectionsPanel && window.sectionsPanel.sections) {
                const section = window.sectionsPanel.sections.find(s => String(s.id) === String(sectionId));
                if (section && (section.title || section.section_heading)) {
                    sectionTitle = section.title || section.section_heading || sectionTitle;
                    // Truncate if too long
                    if (sectionTitle.length > 40) {
                        sectionTitle = sectionTitle.substring(0, 37) + '...';
                    }
                }
            }
        } catch (e) {
            console.warn('[BatchProgressPanel] Could not get section title:', e);
        }
        
        div.innerHTML = `
            <div class="section-result-info">
                <div class="section-result-title">${sectionTitle}</div>
                <div class="section-result-status ${sectionData.status}">
                    ${statusText} ${duration ? `(${duration})` : ''}
                </div>
            </div>
            <div class="section-result-progress">
                <div class="section-progress-bar">
                    <div class="section-progress-fill" style="width: ${sectionData.progress}%"></div>
                </div>
                <div class="section-progress-text">${sectionData.progress}%</div>
                <div class="status-icon ${sectionData.status}">${statusIcon}</div>
            </div>
        `;
        
        return div;
    }

    getStatusIcon(status) {
        const icons = {
            'pending': '⏳',
            'processing': '⚙️',
            'completed': '✅',
            'error': '❌'
        };
        return icons[status] || '⏳';
    }

    getStatusText(status) {
        const texts = {
            'pending': 'Pending',
            'processing': 'Processing',
            'completed': 'Completed',
            'error': 'Error'
        };
        return texts[status] || 'Unknown';
    }

    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) {
            return `${seconds}s`;
        }
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    }

    restoreAccordionState() {
        const savedState = localStorage.getItem('batch-progress-accordion-state');
        if (savedState === 'open') {
            const content = document.getElementById('batch-progress-accordion-content');
            const icon = document.getElementById('batch-progress-accordion-icon');
            if (content && icon) {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        }
    }

    // Public API methods
    getCurrentBatch() {
        return this.currentBatch;
    }

    getSectionProgress(sectionId) {
        return this.sectionProgress.get(sectionId);
    }

    isBatchActive() {
        return this.currentBatch !== null;
    }
}

// Accordion function for batch progress panel
function toggleBatchProgressAccordion() {
    const content = document.getElementById('batch-progress-accordion-content');
    const icon = document.getElementById('batch-progress-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('batch-progress-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('batch-progress-accordion-state', 'closed');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BatchProgressPanel;
}
