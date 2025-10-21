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
            'sdxl-lora': { limit: 400, style: 'Loading...' },
            'dall-e-3': { limit: 4000, style: 'Loading...' },
            'dall-e-2': { limit: 1000, style: 'Loading...' },
            'gpt-image-1': { limit: 2000, style: 'Loading...' }
        };
        this.isEditMode = false;
        
        this.init();
    }

    init() {
        this.loadModelSelection();
        this.loadActiveStyle();
        this.setupEventListeners();
        this.setupAccordion();
        this.setupTransparencyControls();
        
        // Don't load first section here - let the event-driven approach handle it
        // The sections panel will emit a sectionSelected event when it initializes
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

    async loadActiveStyle() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/styles/active`);
            if (response.ok) {
                const data = await response.json();
                const activeStyle = data.active_style;
                
                if (activeStyle && activeStyle.name) {
                    // Update all model configs with the active style name
                    Object.keys(this.modelConfig).forEach(modelKey => {
                        this.modelConfig[modelKey].style = activeStyle.name;
                    });
                    
                    console.log('[PromptBuilderPanel] Loaded active style:', activeStyle.name);
                    this.updateModelDisplay();
                } else {
                    console.log('[PromptBuilderPanel] No active style found, using defaults');
                }
            } else {
                console.error('[PromptBuilderPanel] Error loading active style:', response.status);
            }
        } catch (error) {
            console.error('[PromptBuilderPanel] Error loading active style:', error);
        }
    }

    onStylesLoaded(data) {
        const activeStyle = data.styles?.[data.activeIndex];
        if (activeStyle && activeStyle.name) {
            // Update all model configs with the active style name
            Object.keys(this.modelConfig).forEach(modelKey => {
                this.modelConfig[modelKey].style = activeStyle.name;
            });
            
            console.log('[PromptBuilderPanel] Updated style from styles panel:', activeStyle.name);
            this.updateModelDisplay();
        }
    }

    updateModelDisplay() {
        if (!this.modelSelection) {
            console.log('[PromptBuilderPanel] Model selection not yet loaded, skipping display update');
            return;
        }
        
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
        // Listen for style changes from the styles panel
        document.addEventListener('authoring:styles:loaded', (e) => {
            this.onStylesLoaded(e.detail);
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

        // Preview prompt button
        const previewBtn = document.getElementById('preview-prompt-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.generatePromptPreview());
        }

        // Listen for section selection events
        window.addEventListener('sectionSelected', (event) => {
            if (event.detail && event.detail.section) {
                this.onSectionSelected(event.detail.section);
            }
        });

        // Listen for batch generation events
        window.addEventListener('sections:batch-generate', (event) => {
            this.onBatchGenerate(event.detail.ids);
        });

        // Listen for prompt preview events
        document.addEventListener('authoring:prompt:preview', (event) => {
            this.onPromptPreview(event.detail);
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

    setupTransparencyControls() {
        const compressionCheckbox = document.getElementById('enable-compression');
        const expansionCheckbox = document.getElementById('enable-expansion');
        const compressionWarning = document.getElementById('compression-warning');
        const expansionWarning = document.getElementById('expansion-warning');

        if (compressionCheckbox) {
            compressionCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    compressionWarning.style.display = 'block';
                } else {
                    compressionWarning.style.display = 'none';
                }
            });
        }

        if (expansionCheckbox) {
            expansionCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    expansionWarning.style.display = 'block';
                } else {
                    expansionWarning.style.display = 'none';
                }
            });
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
        console.log('[PromptBuilderPanel] updateCompiledPromptPreview called');
        const textarea = document.getElementById('compiled-prompt-textarea');
        if (!textarea || !this.currentSection) {
            console.log('[PromptBuilderPanel] Missing textarea or currentSection:', { textarea: !!textarea, currentSection: !!this.currentSection });
            return;
        }

        if (this.selectedConceptContent) {
            const config = this.modelConfig[this.modelSelection] || this.modelConfig['sdxl-lora'];
            const compiledPrompt = this.buildCompiledPrompt(this.selectedConceptContent, config);
            textarea.value = compiledPrompt;
            
            // Prepare and display the actual LLM message that will be sent
            this.prepareLLMInputDisplay(compiledPrompt, config);
        } else {
            textarea.value = '';
            this.clearLLMInputDisplay();
        }
        
        this.updateCharacterCount();
    }
    
    async prepareLLMInputDisplay(compiledPrompt, config) {
        console.log('[PromptBuilderPanel] prepareLLMInputDisplay called');
        
        try {
            // Get the system and user prompts from the database
            const response = await fetch('/authoring/api/llm/prompts/image-prompts');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.prompt) {
                    const systemPrompt = data.prompt.system_prompt || '';
                    const userPromptTemplate = data.prompt.prompt_text || '';
                    
                    // Prepare the actual user message with placeholder substitution
                    const userMessage = this.prepareUserMessage(userPromptTemplate, compiledPrompt);
                    
                    // Build the complete LLM message that will be sent
                    let completeMessage = '';
                    if (systemPrompt) {
                        completeMessage += `SYSTEM MESSAGE:\n${systemPrompt}\n\n`;
                    }
                    completeMessage += `USER MESSAGE:\n${userMessage}`;
                    
                    // Update the display
                    const llmInputDisplay = document.getElementById('llm-input-display');
                    if (llmInputDisplay) {
                        llmInputDisplay.value = completeMessage;
                    }
                    
                    console.log('[PromptBuilderPanel] Prepared LLM message:', completeMessage.substring(0, 200) + '...');
                }
            }
        } catch (error) {
            console.error('[PromptBuilderPanel] Error preparing LLM message:', error);
            this.clearLLMInputDisplay();
        }
    }
    
    prepareUserMessage(userPromptTemplate, compiledPrompt) {
        // Replace the [data:selected_concept] placeholder with the compiled prompt
        // This matches the server-side substitution logic
        return userPromptTemplate.replace('[data:selected_concept]', compiledPrompt);
    }
    
    extractStyleDetails(userMessage) {
        // Extract style-related content from the user message
        // This is a simple extraction - could be enhanced
        const styleKeywords = ['watercolor', 'ink', 'brushstrokes', 'pastel', 'margins', 'palette'];
        const lines = userMessage.split('\n');
        const styleLines = lines.filter(line => 
            styleKeywords.some(keyword => line.toLowerCase().includes(keyword))
        );
        
        if (styleLines.length > 0) {
            return styleLines.join('\n');
        } else {
            return 'No explicit style details found in user message';
        }
    }
    
    
    clearLLMInputDisplay() {
        const llmInputDisplay = document.getElementById('llm-input-display');
        if (llmInputDisplay) {
            llmInputDisplay.value = '';
        }
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
        const previewBtn = document.getElementById('preview-prompt-btn');
        
        const hasConceptContent = this.selectedConceptContent !== null;
        
        if (editBtn) editBtn.disabled = !hasConceptContent;
        if (regenerateBtn) regenerateBtn.disabled = !hasConceptContent;
        if (previewBtn) previewBtn.disabled = !hasConceptContent;
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
            
            // Get transparency control values
            const enableCompression = document.getElementById('enable-compression')?.checked ?? true;
            const enableExpansion = document.getElementById('enable-expansion')?.checked ?? false;

            const response = await fetch('/authoring/api/generate-image-prompt-from-builder-v2', {
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
                    style_guidelines: config.style,
                    enable_compression: enableCompression,
                    enable_expansion: enableExpansion
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[PromptBuilderPanel] Prompt generated successfully:', data);
                
                // NEW: Display pipeline transparency information
                this.displayPipelineTransparency(data);
                
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
                // Fetch section data from API (same as individual selection)
                const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${sectionId}`);
                if (!response.ok) {
                    console.warn('[PromptBuilderPanel] Failed to fetch section data for:', sectionId);
                    continue;
                }
                
                const data = await response.json();
                const section = data.section;
                console.log('[DEBUG] Batch: Fetched section data for', sectionId, ':', section);
                
                if (!section || !section.selected_image_concept) {
                    console.warn('[PromptBuilderPanel] Skipping section without concept:', sectionId);
                    continue;
                }

                // Temporarily set current section for generation
                const originalSection = this.currentSection;
                this.currentSection = section;
                
                // Load concept content for this section
                this.loadSelectedConcept(section);
                
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

    onPromptPreview(data) {
        const textarea = document.getElementById('compiled-prompt-textarea');
        if (!textarea) return;
        
        if (data.rendered_prompt) {
            textarea.value = data.rendered_prompt;
            this.updateCharacterCount();
            
            // Show debug info if available
            if (data.debug) {
                console.log('[PromptBuilderPanel] Preview debug:', data.debug);
            }
        } else if (data.error) {
            textarea.value = `Error: ${data.error}`;
            this.updateCharacterCount();
        }
    }

    async generatePromptPreview() {
        if (!this.currentSection) return;
        
        try {
            await window.PromptPreview.renderPreview(this.currentSection.id, this.modelSelection);
        } catch (error) {
            console.error('[PromptBuilderPanel] Error generating preview:', error);
        }
    }

    displayPipelineTransparency(data) {
        const transparencySection = document.getElementById('pipeline-transparency-section');
        if (!transparencySection) return;

        // Show the transparency section
        transparencySection.style.display = 'block';

        // Update summary stats
        const stepsCount = document.getElementById('pipeline-steps-count');
        const finalLength = document.getElementById('pipeline-final-length');
        const compressionUsed = document.getElementById('pipeline-compression-used');
        const expansionUsed = document.getElementById('pipeline-expansion-used');

        if (stepsCount) {
            const stepCount = data.pipeline_steps ? data.pipeline_steps.length : 0;
            stepsCount.textContent = `${stepCount} step${stepCount !== 1 ? 's' : ''}`;
        }

        if (finalLength) {
            finalLength.textContent = `${data.final_length || 0} chars`;
        }

        if (compressionUsed) {
            if (data.compression_used) {
                compressionUsed.textContent = 'Compression used';
                compressionUsed.className = 'status-badge compression-used';
            } else {
                compressionUsed.textContent = 'No compression';
                compressionUsed.className = 'status-badge';
            }
        }

        if (expansionUsed) {
            if (data.expansion_used) {
                expansionUsed.textContent = 'Expansion used';
                expansionUsed.className = 'status-badge expansion-used';
            } else {
                expansionUsed.textContent = 'No expansion';
                expansionUsed.className = 'status-badge';
            }
        }

        // Display pipeline steps
        const stepsContainer = document.getElementById('pipeline-steps-container');
        if (stepsContainer && data.pipeline_steps) {
            stepsContainer.innerHTML = '';
            
            data.pipeline_steps.forEach((step, index) => {
                const stepElement = this.createPipelineStepElement(step, index);
                stepsContainer.appendChild(stepElement);
            });
        }
    }

    createPipelineStepElement(step, index) {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'pipeline-step';

        const stepTitle = this.getStepTitle(step.step);
        const stepMeta = this.getStepMeta(step);

        stepDiv.innerHTML = `
            <div class="pipeline-step-header">
                <div class="pipeline-step-title">${stepTitle}</div>
                <div class="pipeline-step-meta">${stepMeta}</div>
            </div>
            <div class="pipeline-step-content">
                <div class="pipeline-step-input">
                    <div class="pipeline-step-label">Input:</div>
                    <div>${this.truncateText(step.input, 200)}</div>
                </div>
                <div class="pipeline-step-output">
                    <div class="pipeline-step-label">Output:</div>
                    <div>${this.truncateText(step.output, 200)}</div>
                </div>
                ${step.llm_call ? `
                    <div class="pipeline-step-llm-call">
                        <div class="pipeline-step-label">LLM Call:</div>
                        <div><strong>Provider:</strong> ${step.llm_call.provider || 'Unknown'}</div>
                        <div><strong>Model:</strong> ${step.llm_call.model || 'Unknown'}</div>
                        ${step.llm_call.system_prompt ? `<div><strong>System Prompt:</strong> ${this.truncateText(step.llm_call.system_prompt, 100)}</div>` : ''}
                    </div>
                ` : ''}
            </div>
        `;

        return stepDiv;
    }

    getStepTitle(stepType) {
        const titles = {
            'initial_generation': 'Initial Generation',
            'compression': 'Compression',
            'expansion': 'Expansion'
        };
        return titles[stepType] || stepType;
    }

    getStepMeta(step) {
        const inputLength = step.input ? step.input.length : 0;
        const outputLength = step.output ? step.output.length : 0;
        return `${inputLength} → ${outputLength} chars`;
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
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
