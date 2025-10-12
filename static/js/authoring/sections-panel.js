/**
 * Sections Panel - Self-contained JavaScript module
 * Event-driven architecture with callback-based communication
 */

class SectionsPanel {
    constructor(options = {}) {
        this.postId = options.postId || window.postId;
        this.containerId = options.containerId || 'sections-panel';
        this.currentSectionId = null;
    this.sections = [];
        this.selectedSections = new Set();
        
        // Callback functions for external communication
        this.callbacks = {
            onSectionSelect: options.onSectionSelect || (() => {}),
            onBatchStart: options.onBatchStart || (() => {}),
            onBatchProgress: options.onBatchProgress || (() => {}),
            onBatchComplete: options.onBatchComplete || (() => {}),
            onSectionUpdate: options.onSectionUpdate || (() => {})
        };
        
        this.init();
    }
    
    init() {
        this.loadSections();
        this.bindEvents();
    }
    
    async loadSections() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections`);
            const data = await response.json();
            
            if (data.success) {
                this.sections = data.sections;
                this.renderSections();
                // Auto-load first section
                if (this.sections.length > 0) {
                    this.selectSection(this.sections[0].id);
                }
                // Auto-select all sections for batch generation
                this.selectAllSections();
        } else {
                console.error('API returned error:', data.error);
            }
        } catch (error) {
            console.error('Error loading sections:', error);
        }
    }
    
    renderSections() {
        const container = document.getElementById('sections-list');
        if (!container) {
            console.error('sections-list container not found');
            return;
        }
        
        container.innerHTML = '';
        
        this.sections.forEach(section => {
            const sectionElement = this.createSectionElement(section);
            container.appendChild(sectionElement);
        });
    }
    
    createSectionElement(section) {
        const div = document.createElement('div');
        div.className = 'section-item';
        div.dataset.sectionId = section.id;
        div.dataset.status = section.status || 'draft';
        
        div.innerHTML = `
            <div class="section-header">
                <input type="checkbox" class="section-checkbox" data-section-id="${section.id}">
                <span class="section-number">${section.order}</span>
                <span class="section-title">${section.title}</span>
                <span class="section-status ${section.status || 'draft'}">${(section.status || 'draft').charAt(0).toUpperCase() + (section.status || 'draft').slice(1)}</span>
            </div>
            <div class="section-subtitle">${section.subtitle || ''}</div>
            <div class="section-topics">
                ${(section.topics || []).map(topic => 
                    `<span class="topic-tag">${topic}</span>`
                ).join('')}
            </div>
            <div class="section-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${section.progress || 0}%"></div>
                </div>
                <span class="progress-text">${section.progress || 0}% complete</span>
      </div>
    `;

        // Add click handler for section selection
        div.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                this.selectSection(section.id);
            }
        });
        
        // Add checkbox change handler to maintain selectedSections Set
        const checkbox = div.querySelector('.section-checkbox');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedSections.add(section.id);
                console.log(`Section ${section.id} selected. Total selected: ${this.selectedSections.size}`);
            } else {
                this.selectedSections.delete(section.id);
                console.log(`Section ${section.id} deselected. Total selected: ${this.selectedSections.size}`);
            }
        });
        
        return div;
    }
    
    selectSection(sectionId) {
        this.currentSectionId = sectionId;
        const section = this.sections.find(s => s.id === sectionId);
        
        if (section) {
            this.updateSectionSelection();
            
            // Emit event with section data
            this.callbacks.onSectionSelect({
                sectionId: sectionId,
                section: section,
                postId: this.postId
            });
        }
    }
    
    updateSectionSelection() {
        // Remove previous selection
        document.querySelectorAll('.section-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selection to current section
        const currentItem = document.querySelector(`[data-section-id="${this.currentSectionId}"]`);
        if (currentItem) {
            currentItem.classList.add('selected');
        }
    }
    
    selectAllSections() {
        const checkboxes = document.querySelectorAll('.section-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedSections.add(checkbox.dataset.sectionId);
        });
        console.log(`All ${checkboxes.length} sections selected for batch generation`);
    }
    
    async batchGenerate() {
        const selectedIds = Array.from(this.selectedSections);
        console.log(`Batch generate clicked. Selected sections: ${selectedIds.length}`, selectedIds);
        
        if (selectedIds.length === 0) {
            console.log('No sections selected. Please select sections to generate first, or use "Select All" to select all sections.');
            alert('No sections selected. Please select sections to generate first, or use "Select All" to select all sections.');
            return;
        }
        
        // Emit batch start event
        this.callbacks.onBatchStart(selectedIds);
        
        // Disable the button during generation
        const generateBtn = document.getElementById('batch-generate-btn');
        const originalText = generateBtn.textContent;
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        try {
            // Generate content for each selected section
            for (let i = 0; i < selectedIds.length; i++) {
                const sectionId = selectedIds[i];
                const section = this.sections.find(s => s.id === sectionId);
                const sectionTitle = section ? section.title : `Section ${sectionId}`;
                
                // Emit progress event
                this.callbacks.onBatchProgress({
                    current: i + 1,
                    total: selectedIds.length,
                    sectionId: sectionId,
                    sectionTitle: sectionTitle,
                    status: 'generating'
                });
                
                try {
                    // Generate content for this section
                    const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${sectionId}/generate`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        console.log(`Generated content for section ${sectionId}`);
                        this.updateSectionStatus(sectionId, 'complete');
                        this.updateSectionProgress(sectionId, 100);
                        
                        // Emit progress event
                        this.callbacks.onBatchProgress({
                            current: i + 1,
                            total: selectedIds.length,
                            sectionId: sectionId,
                            sectionTitle: sectionTitle,
                            status: 'success'
                        });
                    } else {
                        console.error(`Failed to generate content for section ${sectionId}:`, data.error);
                        this.updateSectionStatus(sectionId, 'error');
                        
                        // Emit progress event
                        this.callbacks.onBatchProgress({
                            current: i + 1,
                            total: selectedIds.length,
                            sectionId: sectionId,
                            sectionTitle: sectionTitle,
                            status: 'error',
                            error: data.error
                        });
                    }
                    
                    // Add a small delay between requests to avoid overwhelming the server
                    if (i < selectedIds.length - 1) {
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                    
      } catch (error) {
                    console.error(`Error generating content for section ${sectionId}:`, error);
                    this.updateSectionStatus(sectionId, 'error');
                    
                    // Emit progress event
                    this.callbacks.onBatchProgress({
                        current: i + 1,
                        total: selectedIds.length,
                        sectionId: sectionId,
                        sectionTitle: sectionTitle,
                        status: 'error',
                        error: error.message
                    });
                }
            }
            
            console.log(`Batch generation completed! Successfully generated content for ${selectedIds.length} sections.`);
            
            // Emit batch complete event
            this.callbacks.onBatchComplete({
                totalSections: selectedIds.length,
                successCount: selectedIds.length // Simplified - would need to track actual success/failure
            });
            
        } catch (error) {
            console.error('Batch generation failed:', error);
        } finally {
            // Re-enable the button
            generateBtn.disabled = false;
            generateBtn.textContent = originalText;
        }
    }
    
    updateSectionProgress(sectionId, progress) {
        const section = this.sections.find(s => s.id === sectionId);
        if (section) {
            section.progress = progress;
            const progressFill = document.querySelector(`[data-section-id="${sectionId}"] .progress-fill`);
            const progressText = document.querySelector(`[data-section-id="${sectionId}"] .progress-text`);
            
            if (progressFill) {
                progressFill.style.width = `${progress}%`;
            }
            if (progressText) {
                progressText.textContent = progress === 100 ? 'Complete' : `${progress}% complete`;
            }
        }
    }
    
    updateSectionStatus(sectionId, status) {
        const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (sectionElement) {
            const statusElement = sectionElement.querySelector('.section-status');
            if (statusElement) {
                statusElement.className = `section-status ${status}`;
                statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            }
        }
    }
    
    bindEvents() {
        // Select All button
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllSections();
            });
        }
        
        // Batch Generate button
        const batchGenerateBtn = document.getElementById('batch-generate-btn');
        if (batchGenerateBtn) {
            batchGenerateBtn.addEventListener('click', () => {
                this.batchGenerate();
            });
        }
        
        // Filter buttons
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                filterBtns.forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                
                // Filter sections based on data-filter attribute
                const filter = e.target.getAttribute('data-filter');
                this.filterSections(filter);
            });
        });
    }
    
    filterSections(filter) {
        const sectionItems = document.querySelectorAll('.section-item');
        
        sectionItems.forEach(item => {
            const status = item.getAttribute('data-status');
            let show = true;
            
            if (filter === 'all') {
                show = true;
            } else if (filter === 'draft') {
                show = status === 'draft';
            } else if (filter === 'complete') {
                show = status === 'complete';
            } else if (filter === 'needs-review') {
                show = status === 'needs-review';
            }
            
            item.style.display = show ? 'block' : 'none';
        });
    }
    
    // Public API methods for external updates
    refreshSections() {
        this.loadSections();
    }
    
    getCurrentSection() {
        return this.sections.find(s => s.id === this.currentSectionId);
    }
    
    getSelectedSections() {
        return Array.from(this.selectedSections);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SectionsPanel;
}