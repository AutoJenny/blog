/**
 * Header Prompt Builder Panel for Image Prompts
 * Adapted for header stage with model selection communication
 */

class HeaderPromptBuilderPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentModel = 'sdxl-lora'; // Default
        this.modelConfig = {
            'sdxl-lora': { limit: 400, style: 'inkwash and watercolour' },
            'dall-e-3': { limit: 4000, style: 'photorealistic' },
            'dall-e-2': { limit: 1000, style: 'artistic' },
            'gpt-image': { limit: 2000, style: 'detailed descriptive' }
        };
        this.isEditMode = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccordion();
        this.updateModelDisplay();
        this.loadAllImageConcepts();
        console.log('[HeaderPromptBuilderPanel] Initialized for post:', this.postId);
    }

    setupEventListeners() {
        // Listen for model selection changes from Model Selection panel
        document.addEventListener('modelSelectionChanged', (event) => {
            console.log('[HeaderPromptBuilderPanel] Model selection changed:', event.detail);
            this.currentModel = event.detail.model;
            this.updateModelDisplay();
        });

        // Edit compiled prompt button
        const editBtn = document.getElementById('edit-compiled-prompt-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.toggleEditMode());
        }

        // Regenerate compiled prompt button
        const regenerateBtn = document.getElementById('regenerate-compiled-prompt-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.generatePrompt());
        }

        // Character count monitoring
        const textarea = document.getElementById('compiled-prompt-textarea');
        if (textarea) {
            textarea.addEventListener('input', () => this.updateCharacterCount());
        }
    }

    setupAccordion() {
        const header = document.querySelector('#prompt-builder-panel .panel-header');
        const content = document.getElementById('prompt-builder-accordion-content');
        const icon = document.getElementById('prompt-builder-accordion-icon');

        if (header && content && icon) {
            // Restore accordion state from DB
            this.restoreAccordionState();
            
            header.addEventListener('click', () => {
                this.toggleAccordion();
            });
        }
    }

    async restoreAccordionState() {
        try {
            const key = `prompt-builder-accordion-state-header-image-prompts`;
            const resp = await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`);
            const data = await resp.json();
            const state = data && data.value ? (typeof data.value === 'string' ? data.value : (data.value.state||'')) : '';
            
            const content = document.getElementById('prompt-builder-accordion-content');
            const icon = document.getElementById('prompt-builder-accordion-icon');
            
            if (state === 'open') {
                if (content && icon) {
                    content.style.display = 'block';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            } else {
                if (content && icon) {
                    content.style.display = 'none';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            }
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error restoring accordion state:', error);
        }
    }

    async toggleAccordion() {
        const content = document.getElementById('prompt-builder-accordion-content');
        const icon = document.getElementById('prompt-builder-accordion-icon');
        
        if (!content || !icon) return;

        const isCollapsed = content.style.display === 'none';
        
        if (isCollapsed) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            // Save open state to DB
            try {
                const key = `prompt-builder-accordion-state-header-image-prompts`;
                await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'open' })
                });
            } catch (error) {
                console.error('[HeaderPromptBuilderPanel] Error saving accordion state:', error);
            }
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            // Save closed state to DB
            try {
                const key = `prompt-builder-accordion-state-header-image-prompts`;
                await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'closed' })
                });
            } catch (error) {
                console.error('[HeaderPromptBuilderPanel] Error saving accordion state:', error);
            }
        }
    }

    async loadAllImageConcepts() {
        try {
            console.log('[HeaderPromptBuilderPanel] Loading all image concepts for post:', this.postId);
            
            // Fetch all sections for this post
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections`);
            if (!response.ok) {
                throw new Error(`Failed to fetch sections: ${response.status}`);
            }
            
            const data = await response.json();
            const sections = data.sections || [];
            
            console.log('[HeaderPromptBuilderPanel] Found sections:', sections.length);
            
            // Extract only SELECTED image concepts from all sections
            const selectedConcepts = [];
            sections.forEach(section => {
                if (section.image_concepts && section.selected_image_concept) {
                    try {
                        const conceptsData = typeof section.image_concepts === 'string' 
                            ? JSON.parse(section.image_concepts) 
                            : section.image_concepts;
                        
                        if (conceptsData.concepts && Array.isArray(conceptsData.concepts)) {
                            // Find only the SELECTED concept for this section
                            const selectedConcept = conceptsData.concepts.find(
                                concept => concept.concept_id === section.selected_image_concept
                            );
                            
                            if (selectedConcept) {
                                selectedConcepts.push({
                                    section_id: section.id,
                                    section_title: section.title || section.section_heading || `Section ${section.id}`,
                                    concept_id: selectedConcept.concept_id,
                                    concept_title: selectedConcept.concept_title,
                                    concept_description: selectedConcept.concept_description,
                                    concept_mood: selectedConcept.concept_mood,
                                    key_visual_elements: selectedConcept.key_visual_elements
                                });
                            }
                        }
                    } catch (error) {
                        console.warn('[HeaderPromptBuilderPanel] Error parsing concepts for section:', section.id, error);
                    }
                }
            });
            
            console.log('[HeaderPromptBuilderPanel] Extracted selected concepts:', selectedConcepts.length);
            
            // Store concepts for LLM consumption
            this.allImageConcepts = selectedConcepts;
            
            // Update display
            this.updateInputPromptsDisplay(selectedConcepts);
            
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error loading image concepts:', error);
            this.updateInputPromptsDisplay([]);
        }
    }

    updateInputPromptsDisplay(concepts) {
        const display = document.getElementById('input-prompts-display');
        if (!display) return;
        
        if (concepts.length === 0) {
            display.innerHTML = `
                <div class="prompts-placeholder">No selected image concepts found. Please select concepts in the Image Concepts stage first.</div>
            `;
            return;
        }
        
        // Create JSON representation for LLM - only descriptions
        const conceptsJson = {
            total_sections: concepts.length,
            concepts: concepts.map(concept => ({
                section: concept.section_title,
                description: concept.concept_description
            }))
        };
        
        // Store JSON for LLM consumption
        this.conceptsJson = JSON.stringify(conceptsJson, null, 2);
        
        // Display formatted list - only descriptions
        const conceptsList = concepts.map(concept => `
            <div class="concept-item">
                <div class="concept-header">
                    <strong>${concept.section_title}</strong>
                </div>
                <div class="concept-details">
                    <div class="concept-description">${concept.concept_description}</div>
                </div>
            </div>
        `).join('');
        
        display.innerHTML = `
            <div class="concepts-summary">
                <div class="concepts-count">Found ${concepts.length} image concepts from ${new Set(concepts.map(c => c.section_id)).size} sections</div>
                <div class="concepts-list">
                    ${conceptsList}
                </div>
            </div>
        `;
        
        console.log('[HeaderPromptBuilderPanel] Updated input prompts display with', concepts.length, 'concepts');
    }

    updateModelDisplay() {
        const config = this.modelConfig[this.currentModel] || this.modelConfig['sdxl-lora'];
        
        // Update model selection display
        const modelDisplay = document.getElementById('current-model-display');
        if (modelDisplay) {
            modelDisplay.textContent = this.currentModel.toUpperCase();
        }
        
        // Update character limit display
        const limitDisplay = document.getElementById('character-limit-display');
        if (limitDisplay) {
            limitDisplay.textContent = `${config.limit} characters`;
        }
        
        // Update style guidelines display
        const styleDisplay = document.getElementById('style-guidelines-display');
        if (styleDisplay) {
            styleDisplay.textContent = config.style;
        }
        
        // Update character count display
        this.updateCharacterCount();
        
        console.log('[HeaderPromptBuilderPanel] Model display updated for:', this.currentModel);
    }

    updateCharacterCount() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        const countElement = document.getElementById('character-count');
        const statusElement = document.getElementById('character-status');
        
        if (!textarea || !countElement || !statusElement) return;

        const currentLength = textarea.value.length;
        const config = this.modelConfig[this.currentModel] || this.modelConfig['sdxl-lora'];
        const limit = config.limit;
        
        countElement.textContent = `${currentLength} / ${limit} chars`;
        
        // Update status with color coding
        if (currentLength <= limit * 0.8) {
            statusElement.textContent = 'Ready';
            statusElement.className = 'character-status success';
        } else if (currentLength <= limit) {
            statusElement.textContent = 'Near Limit';
            statusElement.className = 'character-status warning';
        } else {
            statusElement.textContent = 'Over Limit';
            statusElement.className = 'character-status error';
        }
    }

    toggleEditMode() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        const editBtn = document.getElementById('edit-compiled-prompt-btn');
        
        if (!textarea || !editBtn) return;

        this.isEditMode = !this.isEditMode;
        
        if (this.isEditMode) {
            textarea.readOnly = false;
            editBtn.textContent = 'Save';
            editBtn.classList.remove('btn-secondary');
            editBtn.classList.add('btn-success');
        } else {
            textarea.readOnly = true;
            editBtn.textContent = 'Edit';
            editBtn.classList.remove('btn-success');
            editBtn.classList.add('btn-secondary');
        }
    }

    async generatePrompt() {
        console.log('[HeaderPromptBuilderPanel] Generate prompt requested');
        
        if (!this.conceptsJson) {
            alert('No image concepts available. Please ensure concepts are generated in the Image Concepts stage first.');
            return;
        }
        
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/compile-header-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    concepts_json: this.conceptsJson,
                    model: this.currentModel
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[HeaderPromptBuilderPanel] Prompt compiled successfully:', data);
                
                // Update compiled prompt display
                const textarea = document.getElementById('compiled-prompt-textarea');
                if (textarea && data.compiled_prompt) {
                    textarea.value = data.compiled_prompt;
                    this.updateCharacterCount();
                }
                
            } else {
                const error = await response.json();
                console.error('[HeaderPromptBuilderPanel] Error compiling prompt:', error);
                alert('Error compiling prompt: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error generating prompt:', error);
            alert('Error generating prompt: ' + error.message);
        }
    }
}

// Global accordion function
function togglePromptBuilderAccordion() {
    if (window.headerPromptBuilderPanel) {
        window.headerPromptBuilderPanel.toggleAccordion();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'header-image') {
        window.headerPromptBuilderPanel = new HeaderPromptBuilderPanel(window.postId);
    }
});
