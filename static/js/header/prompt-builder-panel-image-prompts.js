/**
 * Header Prompt Builder Panel for Image Prompts
 * Adapted for header stage with model selection communication
 */

console.log('[HeaderPromptBuilderPanel] Script loaded');

class HeaderPromptBuilderPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentModel = 'gpt-image-1'; // Default
        this.modelConfig = {
            'sdxl-lora': { limit: 400, style: 'inkwash and watercolour' },
            'dall-e-3': { limit: 4000, style: 'photorealistic' },
            'dall-e-2': { limit: 1000, style: 'artistic' },
            'gpt-image-1': { limit: 4000, style: 'pen and ink watercolor' }
        };
        this.isEditMode = false;
        this.loadedSections = []; // Store loaded section data
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccordion();
        this.loadAllImageConcepts();
        this.loadPromptAssemblyData();
        console.log('[HeaderPromptBuilderPanel] Initialized for post:', this.postId);
    }

    setupEventListeners() {
        // Listen for model selection changes from Model Selection panel
        document.addEventListener('modelSelectionChanged', (event) => {
            console.log('[HeaderPromptBuilderPanel] Model selection changed:', event.detail);
            this.currentModel = event.detail.model;
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

        // Prompt Assembly event listeners
        const assemblyModelSelect = document.getElementById('assembly-model-select');
        if (assemblyModelSelect) {
            assemblyModelSelect.addEventListener('change', () => this.updateAssemblyStyleSettings());
        }

        // Requirements checkboxes
        const reqCheckboxes = document.querySelectorAll('.requirements-checklist input[type="checkbox"]');
        reqCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateAssemblyStyleSettings());
        });
    }

    setupAccordion() {
        const content = document.getElementById('prompt-builder-accordion-content');
        const icon = document.getElementById('prompt-builder-accordion-icon');

        if (content && icon) {
            // Wait for HeaderAccordionManager to be available
            if (window.headerAccordionManager) {
                window.headerAccordionManager.initializeAccordion(
                    'prompt-builder',
                    'prompt-builder-accordion-content',
                    'prompt-builder-accordion-icon'
                );
            } else {
                // Retry after a short delay if manager isn't ready
                setTimeout(() => this.setupAccordion(), 100);
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
                <div class="concept-description">${concept.concept_description}</div>
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

    // Prompt Assembly Methods
    async loadPromptAssemblyData() {
        try {
            console.log('[HeaderPromptBuilderPanel] Loading prompt assembly data for post:', this.postId);
            
            const url = `/header/api/posts/${this.postId}/prompt-assembly-data`;
            console.log('[HeaderPromptBuilderPanel] Fetching from URL:', url);
            
            const response = await fetch(url);
            console.log('[HeaderPromptBuilderPanel] Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch prompt assembly data: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('[HeaderPromptBuilderPanel] Prompt assembly data loaded:', data);
            
            // Store sections for later use
            this.loadedSections = data.sections || [];
            
            // Update Step 1: Section Prompts
            console.log('[HeaderPromptBuilderPanel] Updating section prompts display...');
            this.updateSectionPromptsDisplay(this.loadedSections);
            
            // Update Step 2: System Instructions
            console.log('[HeaderPromptBuilderPanel] Updating system prompt display...');
            this.updateSystemPromptDisplay(data.system_prompt || '');
            
            // Update Step 3: Task Template (this also triggers Step 4 update)
            console.log('[HeaderPromptBuilderPanel] Updating task template display...');
            // Store task prompt to use after textareas are created
            const taskPrompt = data.task_prompt || '';
            this.updateTaskTemplateDisplay(taskPrompt);
            
            // Update Step 4: Compiled Result - Force update after a brief delay to ensure textareas exist
            setTimeout(() => {
                console.log('[HeaderPromptBuilderPanel] Updating compiled result with actual data...');
                this.updateCompiledResultDisplay(taskPrompt);
            }, 100);
            
            // Enable preview button
            const previewBtn = document.getElementById('preview-assembly-btn');
            if (previewBtn) {
                previewBtn.disabled = false;
            }
            
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error loading prompt assembly data:', error);
            this.showAssemblyError('Failed to load prompt assembly data');
        }
    }

    updateSectionPromptsDisplay(sections) {
        const container = document.getElementById('section-prompts-container');
        if (!container) return;
        
        if (sections.length === 0) {
            container.innerHTML = '<div class="loading-placeholder">No section prompts found</div>';
            return;
        }
        
        const promptsHtml = sections.map(section => `
            <div class="section-prompt-item">
                <div class="section-prompt-header">${section.section_title}</div>
                <textarea class="section-prompt-text" data-section-order="${section.section_order}">${section.image_prompt}</textarea>
            </div>
        `).join('');
        
        container.innerHTML = promptsHtml;
        
        // Add event listeners to editable textareas
        const textareas = container.querySelectorAll('.section-prompt-text');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', () => this.updateAssemblyStyleSettings());
        });
    }

    updateSystemPromptDisplay(systemPrompt) {
        const display = document.getElementById('system-prompt-display');
        if (!display) return;
        
        display.textContent = systemPrompt || 'System prompt not found';
    }

    updateTaskTemplateDisplay(taskPrompt) {
        const display = document.getElementById('task-template-display');
        if (!display) return;
        
        // Highlight placeholders in the template
        let formattedPrompt = taskPrompt || 'Task template not found';
        
        // Highlight {section_prompts} placeholder
        formattedPrompt = formattedPrompt.replace(
            /\{section_prompts\}/g, 
            '<span class="template-placeholder">{section_prompts}</span>'
        );
        
        // Highlight {style_guidelines} placeholder
        formattedPrompt = formattedPrompt.replace(
            /\{style_guidelines\}/g, 
            '<span class="template-placeholder">{style_guidelines}</span>'
        );
        
        // Highlight {model} placeholder
        formattedPrompt = formattedPrompt.replace(
            /\{model\}/g, 
            '<span class="template-placeholder">{model}</span>'
        );
        
        display.innerHTML = formattedPrompt;
        
        // Automatically update Step 4 with compiled result
        this.updateCompiledResultDisplay(taskPrompt);
    }

    updateCompiledResultDisplay(taskPrompt) {
        const compiledResult = document.getElementById('compiled-result');
        if (!compiledResult) {
            console.log('[HeaderPromptBuilderPanel] compiled-result element not found');
            return;
        }
        
        // Get actual data to replace placeholders
        // First try to get from textareas (if Step 1 exists)
        let sectionPrompts = this.getSectionPromptsFromAssembly();
        console.log('[HeaderPromptBuilderPanel] Section prompts from textareas:', sectionPrompts.length);
        
        // If no textareas, use loaded data directly
        if (sectionPrompts.length === 0 && this.loadedSections && this.loadedSections.length > 0) {
            console.log('[HeaderPromptBuilderPanel] Using loaded sections data:', this.loadedSections.length);
            sectionPrompts = this.loadedSections.map(section => ({
                order: section.section_order,
                prompt: section.image_prompt
            }));
        }
        
        const modelSelect = document.getElementById('assembly-model-select');
        const selectedModel = modelSelect ? modelSelect.value : 'gpt-image-1';
        
        // Replace placeholders with actual data
        let compiledPrompt = taskPrompt || 'Task template not found';
        
        // Replace {section_prompts} with actual section prompts
        if (sectionPrompts.length > 0) {
            // Format: "Section 1: prompt text\n\nSection 2: prompt text\n\n..."
            const promptsText = sectionPrompts.map(section => 
                `Section ${section.order}: ${section.prompt}`
            ).join('\n\n');
            console.log('[HeaderPromptBuilderPanel] Replacing {section_prompts} with', sectionPrompts.length, 'sections');
            compiledPrompt = compiledPrompt.replace(/\{section_prompts\}/g, promptsText);
        } else {
            console.log('[HeaderPromptBuilderPanel] WARNING: No section prompts available');
        }
        
        // Replace {model} with selected model
        compiledPrompt = compiledPrompt.replace(/\{model\}/g, selectedModel);
        
        // Replace {style_guidelines} with current requirements
        const requirements = this.getCurrentRequirements();
        compiledPrompt = compiledPrompt.replace(/\{style_guidelines\}/g, requirements);
        
        console.log('[HeaderPromptBuilderPanel] Final compiled prompt length:', compiledPrompt.length);
        // Use textContent to preserve newlines and formatting
        compiledResult.textContent = compiledPrompt;
    }

    getCurrentRequirements() {
        const checkboxes = document.querySelectorAll('.requirements-checklist input[type="checkbox"]:checked');
        const requirements = Array.from(checkboxes).map(cb => cb.nextSibling.textContent.trim());
        return requirements.join(', ');
    }

    updateAssemblyStyleSettings() {
        const modelSelect = document.getElementById('assembly-model-select');
        const reqCheckboxes = document.querySelectorAll('.requirements-checklist input[type="checkbox"]');
        
        if (!modelSelect || !reqCheckboxes.length) return;
        
        const selectedModel = modelSelect.value;
        const checkedRequirements = Array.from(reqCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.nextSibling.textContent.trim());
        
        // Update Step 4 with current settings
        const taskTemplate = document.getElementById('task-template-display');
        if (taskTemplate) {
            const taskPrompt = taskTemplate.textContent || taskTemplate.innerText;
            this.updateCompiledResultDisplay(taskPrompt);
        }
        
        console.log('[HeaderPromptBuilderPanel] Assembly style settings updated:', {
            model: selectedModel,
            requirements: checkedRequirements
        });
    }

    previewAssemblyTemplate() {
        const sections = this.getSectionPromptsFromAssembly();
        const modelSelect = document.getElementById('assembly-model-select');
        const taskTemplateDisplay = document.getElementById('task-template-display');
        
        if (!sections.length || !modelSelect || !taskTemplateDisplay) {
            alert('Unable to preview template - missing data');
            return;
        }
        
        // Format section prompts for preview
        const sectionPromptsText = sections.map(section => 
            `Section ${section.order}: ${section.prompt}`
        ).join('\n\n');
        
        // Get style guidelines based on model
        const selectedModel = modelSelect.value;
        let styleGuidelines = '';
        if (selectedModel === 'dall-e-3') {
            styleGuidelines = "Use 'photorealistic' style with brushstrokes fading to white edges";
        } else if (selectedModel === 'sdxl') {
            styleGuidelines = "Use 'inkwash and watercolour' style with brushstrokes fading to white edges";
        }
        
        // Show preview in compiled result
        const compiledResult = document.getElementById('compiled-result');
        if (compiledResult) {
            const previewText = `PREVIEW - Template filled with current data:\n\n` +
                `Section Prompts:\n${sectionPromptsText}\n\n` +
                `Style Guidelines: ${styleGuidelines}\n\n` +
                `Model: ${selectedModel}`;
            
            compiledResult.textContent = previewText;
        }
    }

    getSectionPromptsFromAssembly() {
        const textareas = document.querySelectorAll('.section-prompt-text');
        return Array.from(textareas).map(textarea => ({
            order: textarea.dataset.sectionOrder,
            prompt: textarea.value.trim()
        })).filter(section => section.prompt);
    }

    async compileAssemblyPrompt() {
        try {
            console.log('[HeaderPromptBuilderPanel] Compiling assembly prompt...');
            
            const sections = this.getSectionPromptsFromAssembly();
            if (sections.length === 0) {
                alert('No section prompts available to compile');
                return;
            }
            
            const modelSelect = document.getElementById('assembly-model-select');
            const selectedModel = modelSelect ? modelSelect.value : 'dall-e-3';
            
            // Format section prompts for API
            const sectionPromptsText = sections.map(section => 
                `Section ${section.order}: ${section.prompt}`
            ).join('\n\n');
            
            const response = await fetch(`/header/api/posts/${this.postId}/compile-header-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: selectedModel,
                    section_prompts: sectionPromptsText
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[HeaderPromptBuilderPanel] Assembly prompt compiled:', data);
                
                // Update compiled result display
                const compiledResult = document.getElementById('compiled-result');
                if (compiledResult && data.compiled_prompt) {
                    compiledResult.textContent = data.compiled_prompt;
                }
                
                // Update main compiled prompt textarea
                const textarea = document.getElementById('compiled-prompt-textarea');
                if (textarea && data.compiled_prompt) {
                    textarea.value = data.compiled_prompt;
                    this.updateCharacterCount();
                }
                
            } else {
                const error = await response.json();
                console.error('[HeaderPromptBuilderPanel] Error compiling assembly prompt:', error);
                this.showAssemblyError('Error compiling prompt: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error compiling assembly prompt:', error);
            this.showAssemblyError('Error compiling prompt: ' + error.message);
        }
    }

    showAssemblyError(message) {
        const compiledResult = document.getElementById('compiled-result');
        if (compiledResult) {
            compiledResult.textContent = `ERROR: ${message}`;
            compiledResult.style.color = '#f44336';
        }
    }
}

// Global accordion function fallback
window.togglePromptBuilderAccordion = function() {
    console.log('[HeaderPromptBuilderPanel] togglePromptBuilderAccordion called');
    // This function will be replaced by HeaderAccordionManager when it initializes
    if (window.headerPromptBuilderPanel) {
        // Try to call the accordion manager's function if it exists
        const managerFunc = window['togglePromptBuilderAccordion'];
        if (managerFunc && typeof managerFunc === 'function') {
            managerFunc();
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[HeaderPromptBuilderPanel] DOM loaded, checking initialization...');
    console.log('[HeaderPromptBuilderPanel] window.postId:', window.postId);
    console.log('[HeaderPromptBuilderPanel] window.currentSubstage:', window.currentSubstage);
    
    if (window.postId && window.currentSubstage === 'header-image') {
        console.log('[HeaderPromptBuilderPanel] Initializing panel...');
        window.headerPromptBuilderPanel = new HeaderPromptBuilderPanel(window.postId);
        console.log('[HeaderPromptBuilderPanel] Panel initialized:', window.headerPromptBuilderPanel);
    } else {
        console.log('[HeaderPromptBuilderPanel] Not initializing - missing postId or wrong substage');
    }
});

