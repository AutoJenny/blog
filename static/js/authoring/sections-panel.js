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
        this.checkOllamaStatus();
        // Check Ollama status every 30 seconds
        setInterval(() => this.checkOllamaStatus(), 30000);
    }
    
    async checkOllamaStatus() {
        try {
            const response = await fetch('/api/ollama/status');
            const data = await response.json();
            
            const indicator = document.getElementById('ollama-status-indicator');
            const icon = document.getElementById('ollama-status-icon');
            const text = document.getElementById('ollama-status-text');
            const startBtn = document.getElementById('ollama-start-btn');
            const generateBtn = document.getElementById('batch-generate-btn');
            
            if (!indicator || !icon || !text) return;
            
            if (data.is_running) {
                indicator.style.display = 'block';
                indicator.style.backgroundColor = '#10b981';
                indicator.style.color = '#fff';
                icon.innerHTML = '<i class="fas fa-check-circle"></i>';
                text.textContent = 'Ollama is running';
                if (startBtn) startBtn.style.display = 'none';
                if (generateBtn) generateBtn.disabled = false;
            } else {
                indicator.style.display = 'block';
                indicator.style.backgroundColor = '#ef4444';
                indicator.style.color = '#fff';
                icon.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
                text.textContent = 'Ollama is not running';
                if (startBtn) {
                    startBtn.style.display = 'inline-block';
                    startBtn.onclick = () => {
                        alert('To start Ollama, run: ollama serve\nOr check if Ollama is installed and running on http://localhost:11434');
                    };
                }
                if (generateBtn) {
                    generateBtn.disabled = true;
                    generateBtn.title = 'Ollama must be running to generate prompts';
                }
            }
        } catch (error) {
            console.error('Error checking Ollama status:', error);
        }
    }
    
    async loadSections() {
        try {
            // Determine the correct API endpoint based on current stage
            let apiEndpoint = window.currentStage === 'imaging' 
                ? `/imaging/api/posts/${this.postId}/sections`
                : `/authoring/api/posts/${this.postId}/sections`;
            
            // Add image_context parameter if we're in image captions or image generation context (check both hyphenated and underscored variants)
            const currentSubstage = window.currentSubstage;
            if (currentSubstage === 'image-captions' || currentSubstage === 'image_captions' || currentSubstage === 'image-generation') {
                const separator = apiEndpoint.includes('?') ? '&' : '?';
                apiEndpoint += `${separator}image_context=true`;
            }
            
            const response = await fetch(apiEndpoint);
            const data = await response.json();
            
            if (data.success) {
                this.sections = data.sections;
                
                // Map imaging API format to authoring API format if needed
                if (window.currentStage === 'imaging') {
                    this.sections = this.sections.map(section => ({
                        id: section.id,
                        title: section.section_heading || `Section ${section.id}`,
                        subtitle: section.section_description || '',
                        order: section.section_order || section.id,
                        status: 'draft', // Default status for imaging
                        topics: [], // No topics in imaging API
                        ...section // Keep original fields
                    }));
                }
                
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
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    createSectionElement(section) {
        const div = document.createElement('div');
        div.className = 'section-item';
        div.dataset.sectionId = section.id;
        div.dataset.status = section.status || 'draft';
        
        // Build data chunks display for profile posts
        let dataChunksHtml = '';
        if (section.data_chunks && section.data_chunks.length > 0) {
            dataChunksHtml = `
                <div class="section-data-chunks">
                    <div class="data-chunks-header">
                        <i class="fas fa-database"></i> Raw Data (${section.data_chunks.length} chunks)
                    </div>
                    <div class="data-chunks-list">
                        ${section.data_chunks.slice(0, 5).map(chunk => `
                            <div class="data-chunk-item" data-category="${chunk.category || 'data'}">
                                <div class="data-chunk-title">${this.escapeHtml(chunk.topic_title || chunk.title || 'Data Chunk')}</div>
                                <div class="data-chunk-source">${this.escapeHtml(chunk.source || 'unknown')}</div>
                                ${chunk.description ? `<div class="data-chunk-preview">${this.escapeHtml(chunk.description.substring(0, 100))}${chunk.description.length > 100 ? '...' : ''}</div>` : ''}
                            </div>
                        `).join('')}
                        ${section.data_chunks.length > 5 ? `<div class="data-chunks-more">+ ${section.data_chunks.length - 5} more chunks</div>` : ''}
                    </div>
                </div>
            `;
        }
        
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
            ${dataChunksHtml}
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
            
            // Emit custom event for other panels to listen to
            window.dispatchEvent(new CustomEvent('sectionSelected', {
                detail: {
                    sectionId: sectionId,
                    section: section,
                    postId: this.postId
                }
            }));
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
            // Check Ollama status before starting batch generation
            const ollamaStatus = await fetch('/api/ollama/status').then(r => r.json());
            if (!ollamaStatus.is_running) {
                this.showError('Ollama is not running. Please start Ollama before generating prompts.\n\nTo start Ollama, run: ollama serve\nOr check if Ollama is installed and running on http://localhost:11434');
                generateBtn.disabled = false;
                generateBtn.textContent = originalText;
                return;
            }
            
            // For image-prompts substage, use the same logic as individual Generate button
            // Check for both hyphenated and underscored variants
            const currentSubstage = window.currentSubstage;
            if (currentSubstage === 'image-prompts' || currentSubstage === 'image_prompts') {
                await this.batchGenerateImagePrompts(selectedIds);
            } else if (currentSubstage === 'image-concepts' || currentSubstage === 'image_concepts') {
                // For image-concepts, dispatch event so output panel can handle it
                // Don't re-enable button here - output panel will handle it
                console.log('[DEBUG] SectionsPanel: Dispatching sections:batch-generate event for image-concepts with IDs:', selectedIds);
                const event = new CustomEvent('sections:batch-generate', {
                    detail: { ids: selectedIds },
                    bubbles: true
                });
                // Dispatch on both window and document to ensure listeners catch it
                window.dispatchEvent(event);
                document.dispatchEvent(event);
                console.log('[DEBUG] SectionsPanel: Event dispatched on both window and document, waiting for output panel to handle');
                // Wait for batch completion - output panel will re-enable button
                return; // Exit early, button will be re-enabled by output panel
            } else {
                // For other substages, use the original batch generation logic
                await this.batchGenerateOther(selectedIds);
            }
            
            console.log(`Batch generation completed! Successfully generated content for ${selectedIds.length} sections.`);
            
            // Reload all sections to get updated data
            await this.loadSections();
            
            // Emit batch complete event
            this.callbacks.onBatchComplete({
                totalSections: selectedIds.length,
                successCount: selectedIds.length // Simplified - would need to track actual success/failure
            });
            
        } catch (error) {
            console.error('Batch generation failed:', error);
            this.showError(`Batch generation failed: ${error.message || 'Unknown error'}`);
        } finally {
            // Re-enable the button
            generateBtn.disabled = false;
            generateBtn.textContent = originalText;
        }
    }
    
    async batchGenerateImagePrompts(selectedIds) {
        // Use the same logic as the individual Generate button for each section
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
                status: 'generating',
                progress: 0
            });
            
            try {
                // Get the compiled prompt from the section (same as individual Generate button)
                let compiledPrompt = `Generate image prompt for section ${sectionId}`;
                
                if (section && section.image_concepts) {
                    try {
                        // image_concepts might already be parsed or might be a string
                        let conceptsData = section.image_concepts;
                        if (typeof conceptsData === 'string') {
                            conceptsData = JSON.parse(conceptsData);
                        }
                        
                        if (conceptsData.concepts && conceptsData.concepts.length > 0) {
                            const selectedConceptId = section.selected_image_concept || 'CONCEPT-1';
                            const selectedConcept = conceptsData.concepts.find(c => c.concept_id === selectedConceptId);
                            if (selectedConcept) {
                                compiledPrompt = selectedConcept.concept_description || compiledPrompt;
                            }
                        }
                    } catch (e) {
                        console.warn(`Could not parse image concepts for section ${sectionId}:`, e);
                    }
                }
                
                // Use the same API call as individual Generate button
                const response = await fetch('/authoring/api/generate-image-prompt-from-builder-v2', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        post_id: this.postId,
                        section_id: sectionId,
                        compiled_prompt: compiledPrompt,
                        enable_compression: true,
                        enable_expansion: false,
                        llm_provider: 'Ollama',
                        llm_model: 'llama3.2:latest'
                    })
                });
                
                console.log(`[Batch Generate] Response status: ${response.status} for section ${sectionId}`);
                
                let data;
                try {
                    data = await response.json();
                } catch (jsonError) {
                    // If response is not JSON, create error object
                    const text = await response.text();
                    throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
                }
                
                console.log(`[Batch Generate] Response data for section ${sectionId}:`, data);
                
                if (!response.ok || !data.success) {
                    const errorMsg = data.error || `HTTP ${response.status}: ${response.statusText}` || 'Unknown error';
                    console.error(`Failed to generate image prompt for section ${sectionId}:`, errorMsg);
                    
                    // Show user-visible error
                    this.showError(`Section ${sectionTitle}: ${errorMsg}`);
                    
                    this.updateSectionStatus(sectionId, 'error');
                    
                    // Emit progress event
                    this.callbacks.onBatchProgress({
                        current: i + 1,
                        total: selectedIds.length,
                        sectionId: sectionId,
                        sectionTitle: sectionTitle,
                        status: 'error',
                        error: errorMsg,
                        progress: 0
                    });
                } else {
                    console.log(`Generated image prompt for section ${sectionId}`);
                    this.updateSectionStatus(sectionId, 'complete');
                    this.updateSectionProgress(sectionId, 100);
                    
                    // Reload section data to get updated image_prompts
                    await this.reloadSectionData(sectionId);
                    
                    // Update output panel if this section is currently displayed
                    if (window.imagePromptsOutputPanel && window.imagePromptsOutputPanel.currentSection && 
                        window.imagePromptsOutputPanel.currentSection.id === sectionId) {
                        const updatedSection = this.sections.find(s => s.id === sectionId || s.id == sectionId);
                        if (updatedSection) {
                            window.imagePromptsOutputPanel.onSectionSelected(updatedSection);
                        }
                    }
                    
                    // Emit progress event
                    this.callbacks.onBatchProgress({
                        current: i + 1,
                        total: selectedIds.length,
                        sectionId: sectionId,
                        sectionTitle: sectionTitle,
                        status: 'success',
                        progress: 100
                    });
                }
                
                // Add a small delay between requests to avoid overwhelming the server
                if (i < selectedIds.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
            } catch (error) {
                console.error(`Error generating image prompt for section ${sectionId}:`, error);
                
                // Show user-visible error
                const errorMsg = error.message || 'Network or server error';
                this.showError(`Section ${sectionTitle}: ${errorMsg}`);
                
                this.updateSectionStatus(sectionId, 'error');
                
                // Emit progress event
                this.callbacks.onBatchProgress({
                    current: i + 1,
                    total: selectedIds.length,
                    sectionId: sectionId,
                    sectionTitle: sectionTitle,
                    status: 'error',
                    error: errorMsg,
                    progress: 0
                });
            }
        }
    }
    
    async batchGenerateOther(selectedIds) {
        // Original batch generation logic for non-image-prompts substages
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
                // Determine API endpoint based on current substage (check both hyphenated and underscored variants)
                let apiEndpoint;
                const currentSubstage = window.currentSubstage;
                if (currentSubstage === 'drafting') {
                    apiEndpoint = `/authoring/api/posts/${this.postId}/sections/${sectionId}/generate`;
                } else if (currentSubstage === 'image-concepts' || currentSubstage === 'image_concepts') {
                    apiEndpoint = `/authoring/api/posts/${this.postId}/sections/${sectionId}/generate-image-concepts`;
                } else if (currentSubstage === 'image-captions' || currentSubstage === 'image_captions') {
                    apiEndpoint = `/authoring/api/posts/${this.postId}/sections/${sectionId}/generate-image-captions`;
                } else {
                    apiEndpoint = `/authoring/api/posts/${this.postId}/sections/${sectionId}/generate`;
                }
                
                console.log(`[Sections Panel] Batch generating for ${window.currentSubstage}, using endpoint: ${apiEndpoint}`);
                
                // Generate content for this section
                const response = await fetch(apiEndpoint, {
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
                    
                    // Reload section data to get the generated content and update output panel
                    try {
                        const sectionResponse = await fetch(`/authoring/api/posts/${this.postId}/sections/${sectionId}`);
                        const sectionData = await sectionResponse.json();
                        if (sectionData.success && sectionData.section) {
                            // Update the section in our local array
                            const sectionIndex = this.sections.findIndex(s => s.id === sectionId);
                            if (sectionIndex !== -1) {
                                this.sections[sectionIndex] = { ...this.sections[sectionIndex], ...sectionData.section };
                            }
                            
                            // Update output panel based on current substage (check both hyphenated and underscored variants)
                            const currentSubstage = window.currentSubstage;
                            if ((currentSubstage === 'image-concepts' || currentSubstage === 'image_concepts') && typeof window.imageConceptsOutputPanel !== 'undefined' && window.imageConceptsOutputPanel) {
                                // For image-concepts, use show() method with proper section data structure
                                const section = sectionData.section;
                                // Map section data to expected format
                                const formattedSection = {
                                    id: section.id || sectionId,
                                    title: section.section_heading || section.title || `Section ${sectionId}`,
                                    subtitle: section.section_description || section.subtitle || '',
                                    order: section.section_order || section.order || sectionId,
                                    topics: section.topics || [],
                                    image_concepts: section.image_concepts || '',
                                    selected_image_concept: section.selected_image_concept || ''
                                };
                                
                                // Update display if:
                                // 1. No section is currently displayed, OR
                                // 2. This is the currently displayed section, OR
                                // 3. This is the first section being generated
                                if (!window.imageConceptsOutputPanel.current || 
                                    window.imageConceptsOutputPanel.current.id === formattedSection.id ||
                                    (i === 0 && !window.imageConceptsOutputPanel.current)) {
                                    window.imageConceptsOutputPanel.show(formattedSection);
                                }
                            } else if (typeof window.outputPanel !== 'undefined' && window.outputPanel) {
                                // For other substages (e.g., drafting), use loadSection()
                                window.outputPanel.loadSection(sectionId, sectionData.section);
                            }
                        }
                    } catch (loadError) {
                        console.warn(`Could not reload section ${sectionId} after generation:`, loadError);
                    }
                    
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
    
    showError(message) {
        // Create or update error notification
        let errorDiv = document.getElementById('batch-generate-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'batch-generate-error';
            errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 1rem; border-radius: 8px; z-index: 10000; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
            errorDiv.innerHTML = '<div style="display: flex; justify-content: space-between; align-items: start;"><div><strong>Generation Error</strong><div style="margin-top: 0.5rem; font-size: 0.875rem; white-space: pre-line;" id="error-message"></div></div><button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer; margin-left: 1rem;">×</button></div>';
            document.body.appendChild(errorDiv);
        }
        
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            const existing = errorMessage.textContent;
            errorMessage.textContent = existing ? `${existing}\n${message}` : message;
        }
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv && errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 10000);
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
    
    async reloadSectionData(sectionId) {
        try {
            // Reload section data from API
            let apiEndpoint = window.currentStage === 'imaging' 
                ? `/imaging/api/posts/${this.postId}/sections`
                : `/authoring/api/posts/${this.postId}/sections`;
            
            const response = await fetch(apiEndpoint);
            const data = await response.json();
            
            if (data.success && data.sections) {
                // Update the section in our local array
                const updatedSection = data.sections.find(s => s.id === sectionId || s.id == sectionId);
                if (updatedSection) {
                    const index = this.sections.findIndex(s => s.id === sectionId || s.id == sectionId);
                    if (index !== -1) {
                        this.sections[index] = updatedSection;
                        // Re-render the section in the list
                        this.renderSections();
                        // Update the display if this section is currently selected
                        if (this.currentSectionId === sectionId || this.currentSectionId == sectionId) {
                            this.selectSection(sectionId);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`Error reloading section data for ${sectionId}:`, error);
        }
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