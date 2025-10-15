/**
 * Prompt Builder Panel for Image Prompts
 * Sophisticated DB-driven prompt generation with character limits and compression
 */

class PromptBuilderPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSection = null;
        this.modelSelection = null;
        this.modelConfig = {
            'sdxl-lora': { limit: 400, style: 'inkwash and watercolour' },
            'dalle-3': { limit: 4000, style: 'photorealistic' },
            'dalle-2': { limit: 1000, style: 'artistic' },
            'gpt-image': { limit: 2000, style: 'detailed descriptive' }
        };
        this.isEditMode = false;
        
        this.init();
    }

    init() {
        this.loadModelSelection();
        this.setupEventListeners();
        this.setupAccordion();
        console.log('[PromptBuilderPanel] Initialized for post:', this.postId);
    }

    async loadModelSelection() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/imaging-model-selection`);
            if (response.ok) {
                const data = await response.json();
                this.modelSelection = data.model_selection || 'sdxl-lora';
            } else {
                this.modelSelection = 'sdxl-lora'; // Default fallback
            }
        } catch (error) {
            console.error('[PromptBuilderPanel] Error loading model selection:', error);
            this.modelSelection = 'sdxl-lora'; // Default fallback
        }
        
        this.updateModelDisplay();
    }

    updateModelDisplay() {
        const config = this.modelConfig[this.modelSelection] || this.modelConfig['sdxl-lora'];
        
        // Update model selection display
        const modelDisplay = document.getElementById('current-model-display');
        if (modelDisplay) {
            modelDisplay.textContent = this.modelSelection.toUpperCase();
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
    }

    setupEventListeners() {
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

        // Listen for section selection events
        window.addEventListener('sectionSelected', (event) => {
            this.onSectionSelected(event.detail.section);
        });

        // Listen for batch generation events
        window.addEventListener('sections:batch-generate', (event) => {
            this.onBatchGenerate(event.detail.ids);
        });

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
            const key = `prompt-builder-accordion-state-image-prompts`;
            const resp = await fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`);
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
            console.error('[PromptBuilderPanel] Error restoring accordion state:', error);
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
                const key = `prompt-builder-accordion-state-image-prompts`;
                await fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'open' })
                });
            } catch (error) {
                console.error('[PromptBuilderPanel] Error saving accordion state:', error);
            }
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            // Save closed state to DB
            try {
                const key = `prompt-builder-accordion-state-image-prompts`;
                await fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'closed' })
                });
            } catch (error) {
                console.error('[PromptBuilderPanel] Error saving accordion state:', error);
            }
        }
    }

    onSectionSelected(section) {
        console.log('[DEBUG] PromptBuilderPanel received section:', section);
        this.currentSection = section;
        this.updateSectionTitle(section.title || section.section_heading || 'Unknown Section');
        this.loadSelectedConcept(section);
        this.updateButtonStates();
        console.log('[PromptBuilderPanel] Section selected:', section.id);
    }

    updateSectionTitle(title) {
        const titleElement = document.getElementById('prompt-builder-section-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    loadSelectedConcept(section) {
        console.log('[DEBUG] loadSelectedConcept called with section:', section);
        const conceptDisplay = document.getElementById('selected-concept-display');
        if (!conceptDisplay) return;

        const selectedConceptId = section.selected_image_concept;
        const imageConcepts = section.image_concepts;
        console.log('[DEBUG] selectedConceptId:', selectedConceptId);
        console.log('[DEBUG] imageConcepts:', imageConcepts);
        
        if (selectedConceptId && imageConcepts) {
            try {
                // Parse the image concepts JSON
                const conceptsData = typeof imageConcepts === 'string' ? JSON.parse(imageConcepts) : imageConcepts;
                console.log('[DEBUG] Parsed conceptsData:', conceptsData);
                
                // Find the selected concept
                let selectedConcept = null;
                if (conceptsData.concepts && Array.isArray(conceptsData.concepts)) {
                    console.log('[DEBUG] Found concepts array with', conceptsData.concepts.length, 'items');
                    selectedConcept = conceptsData.concepts.find(c => c.concept_id === selectedConceptId);
                    console.log('[DEBUG] Found selectedConcept:', selectedConcept);
                } else {
                    console.log('[DEBUG] No concepts array found in conceptsData');
                }
                
                if (selectedConcept) {
                    // Display the descriptive elements (not the title)
                    conceptDisplay.innerHTML = `
                        <div class="concept-text">
                            <div class="concept-description">${selectedConcept.concept_description}</div>
                            <div class="concept-mood">Mood: ${selectedConcept.concept_mood}</div>
                            <div class="concept-elements">Key Elements: ${selectedConcept.key_visual_elements}</div>
                        </div>
                    `;
                    
                    // Store the descriptive content for use in compiled prompt
                    this.selectedConceptContent = {
                        description: selectedConcept.concept_description,
                        mood: selectedConcept.concept_mood,
                        elements: selectedConcept.key_visual_elements
                    };
                    console.log('[DEBUG] Set selectedConceptContent:', this.selectedConceptContent);
                } else {
                    conceptDisplay.innerHTML = `
                        <div class="concept-placeholder">Selected concept "${selectedConceptId}" not found in concepts data.</div>
                    `;
                    this.selectedConceptContent = null;
                }
            } catch (error) {
                console.error('[PromptBuilderPanel] Error parsing image concepts:', error);
                conceptDisplay.innerHTML = `
                    <div class="concept-placeholder">Error parsing concepts data: ${error.message}</div>
                `;
                this.selectedConceptContent = null;
            }
        } else {
            conceptDisplay.innerHTML = `
                <div class="concept-placeholder">No concept selected. Please go to Image Concepts page to select one.</div>
            `;
            this.selectedConceptContent = null;
        }
        
        // Update compiled prompt preview
        this.updateCompiledPromptPreview();
    }

    updateCompiledPromptPreview() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        if (!textarea || !this.currentSection) return;

        if (this.selectedConceptContent) {
            const config = this.modelConfig[this.modelSelection] || this.modelConfig['sdxl-lora'];
            const compiledPrompt = this.buildCompiledPrompt(this.selectedConceptContent, config);
            textarea.value = compiledPrompt;
        } else {
            textarea.value = '';
        }
        
        this.updateCharacterCount();
    }

    buildCompiledPrompt(conceptContent, config) {
        // Build sophisticated prompt with character limit awareness using descriptive content
        const basePrompt = `Create an image showing: ${conceptContent.description}`;
        const moodPrompt = `Mood: ${conceptContent.mood}`;
        const elementsPrompt = `Key Elements: ${conceptContent.elements}`;
        const stylePrompt = `Style: ${config.style}`;
        
        const fullPrompt = `${basePrompt}. ${moodPrompt}. ${elementsPrompt}. ${stylePrompt}`;
        
        // If over limit, truncate intelligently
        if (fullPrompt.length > config.limit) {
            // Prioritize description, then mood, then elements
            let truncatedPrompt = `Create an image showing: ${conceptContent.description}`;
            
            if (truncatedPrompt.length + moodPrompt.length + 2 <= config.limit) {
                truncatedPrompt += `. ${moodPrompt}`;
            }
            
            if (truncatedPrompt.length + stylePrompt.length + 2 <= config.limit) {
                truncatedPrompt += `. ${stylePrompt}`;
            }
            
            return truncatedPrompt;
        }
        
        return fullPrompt;
    }

    updateCharacterCount() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        const countElement = document.getElementById('character-count');
        const statusElement = document.getElementById('character-status');
        
        if (!textarea || !countElement || !statusElement) return;

        const currentLength = textarea.value.length;
        const config = this.modelConfig[this.modelSelection] || this.modelConfig['sdxl-lora'];
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

    updateButtonStates() {
        const editBtn = document.getElementById('edit-compiled-prompt-btn');
        const regenerateBtn = document.getElementById('regenerate-compiled-prompt-btn');
        
        const hasConceptContent = this.selectedConceptContent !== null;
        
        if (editBtn) editBtn.disabled = !hasConceptContent;
        if (regenerateBtn) regenerateBtn.disabled = !hasConceptContent;
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
        if (!this.currentSection || !this.selectedConceptContent) {
            console.warn('[PromptBuilderPanel] No section or concept content selected');
            return;
        }

        const generateBtn = document.getElementById('generate-prompt-btn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }

        try {
            const config = this.modelConfig[this.modelSelection] || this.modelConfig['sdxl-lora'];
            const compiledPrompt = this.buildCompiledPrompt(this.selectedConceptContent, config);
            
            const response = await fetch('/api/generate-image-prompt-from-builder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_id: this.postId,
                    section_id: this.currentSection.id,
                    selected_concept: this.currentSection.selected_image_concept,
                    concept_content: this.selectedConceptContent,
                    imaging_model: this.modelSelection,
                    character_limit: config.limit,
                    compiled_prompt: compiledPrompt,
                    style_guidelines: config.style
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[PromptBuilderPanel] Prompt generated successfully:', data);
                
                // Emit event for output panel
                window.dispatchEvent(new CustomEvent('promptGenerated', {
                    detail: {
                        sectionId: this.currentSection.id,
                        prompt: data.image_prompt || data.prompt,
                        metadata: data
                    }
                }));
                
                // Update compiled prompt display
                const textarea = document.getElementById('compiled-prompt-textarea');
                if (textarea && data.image_prompt) {
                    textarea.value = data.image_prompt;
                    this.updateCharacterCount();
                }
                
            } else {
                const error = await response.json();
                console.error('[PromptBuilderPanel] Error generating prompt:', error);
                alert('Error generating prompt: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[PromptBuilderPanel] Error generating prompt:', error);
            alert('Error generating prompt: ' + error.message);
        } finally {
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Prompt';
            }
        }
    }

    async onBatchGenerate(sectionIds) {
        console.log('[PromptBuilderPanel] Batch generation started for sections:', sectionIds);
        
        // Process each section sequentially
        for (const sectionId of sectionIds) {
            try {
                // Find section data
                const section = window.sectionsData?.find(s => s.id === sectionId);
                if (!section || !section.selected_image_concept) {
                    console.warn('[PromptBuilderPanel] Skipping section without concept:', sectionId);
                    continue;
                }

                // Temporarily set current section for generation
                const originalSection = this.currentSection;
                this.currentSection = section;
                
                // Generate prompt for this section
                await this.generatePrompt();
                
                // Restore original section
                this.currentSection = originalSection;
                
                // Small delay between generations
                await new Promise(resolve => setTimeout(resolve, 1000));
                
            } catch (error) {
                console.error('[PromptBuilderPanel] Error in batch generation for section:', sectionId, error);
            }
        }
        
        console.log('[PromptBuilderPanel] Batch generation completed');
    }
}

// Global accordion function
function togglePromptBuilderAccordion() {
    if (window.promptBuilderPanel) {
        window.promptBuilderPanel.toggleAccordion();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'image-prompts') {
        window.promptBuilderPanel = new PromptBuilderPanel(window.postId);
    }
});
