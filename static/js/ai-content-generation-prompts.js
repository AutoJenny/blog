/**
 * AI Content Generation Prompts Module
 * Prompt management and LLM configuration functions
 */

// Add prompt-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Generate prompt for product or blog section
    generatePrompt(data, contentType) {
        if (this.databasePrompts && this.databasePrompts.user_prompt_template) {
            let prompt = this.databasePrompts.user_prompt_template.value;
            
            // Check if this is a product or blog section based on available fields
            if (data.name && data.description) {
                // Product data
                prompt = prompt.replace(/\{product_name\}/g, data.name || 'Unknown Product');
                prompt = prompt.replace(/\{product_description\}/g, data.description || 'No description available');
                prompt = prompt.replace(/\{product_sku\}/g, data.url || 'URL not available');
                prompt = prompt.replace(/\{content_type\}/g, this.getContentTypeDisplayName(contentType));
            } else if (data.section_title && data.section_content) {
                // Blog section data
                prompt = prompt.replace(/\{section_title\}/g, data.section_title || 'Untitled Section');
                prompt = prompt.replace(/\{section_content\}/g, data.section_content || 'No content available');
                prompt = prompt.replace(/\{post_title\}/g, data.post_title || 'Untitled Post');
                prompt = prompt.replace(/\{post_url\}/g, data.post_url || 'URL not available');
                prompt = prompt.replace(/\{content_type\}/g, this.getContentTypeDisplayName(contentType));
            }
            
            return prompt;
        }
        
        // Fallback
        if (data.name) {
            return `Generate ${this.getContentTypeDisplayName(contentType)} content for ${data.name}`;
        } else if (data.section_title) {
            return `Generate ${this.getContentTypeDisplayName(contentType)} content for ${data.section_title}`;
        }
        
        return 'Select an item to see the generation prompt';
    },
    
    // Update generation prompt display
    updateGenerationPromptDisplay() {
        const promptDisplay = document.getElementById('llm-generation-prompt');
        const systemPromptElement = document.getElementById('llm-system-prompt');
        
        // Update system prompt from database
        if (this.databasePrompts && this.databasePrompts.system_prompt && systemPromptElement) {
            systemPromptElement.value = this.databasePrompts.system_prompt.value;
        }
        
        // Update generation prompt
        if (this.selectedData) {
            const prompt = this.generatePrompt(this.selectedData, this.selectedContentType);
            if (promptDisplay) {
                promptDisplay.value = prompt;
            }
        } else {
            if (promptDisplay) {
                promptDisplay.value = 'Select an item to see the generation prompt';
            }
        }
    },
    
    // Toggle prompt edit mode
    togglePromptEdit() {
        const promptTextarea = document.getElementById('llm-generation-prompt');
        const editBtn = document.getElementById('edit-generation-prompt-btn');
        
        if (this.isPromptEditMode) {
            // Save mode - save the prompt
            const promptText = promptTextarea.value;
            this.savePromptTemplate(promptText);
            
            // Switch back to readonly mode
            this.isPromptEditMode = false;
            promptTextarea.readOnly = true;
            editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
        } else {
            // Edit mode - make textarea editable
            this.isPromptEditMode = true;
            promptTextarea.readOnly = false;
            editBtn.innerHTML = '<i class="fas fa-save"></i> Save';
            
            // Populate textarea with current prompt template
            if (this.databasePrompts && this.databasePrompts.user_prompt_template) {
                promptTextarea.value = this.databasePrompts.user_prompt_template.value;
            }
            
            promptTextarea.focus();
        }
    },
    
    // Setup LLM controls (temperature slider, etc.)
    setupLLMControls() {
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureValue = document.getElementById('temperature-value');
        
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
        }
    }
});
