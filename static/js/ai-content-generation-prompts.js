/**
 * AI Content Generation Prompts Module
 * Prompt management and LLM configuration functions
 */

// Add prompt-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Generate prompt for product
    generatePromptForProduct(product, contentType) {
        if (this.databasePrompts && this.databasePrompts.user_prompt_template) {
            let prompt = this.databasePrompts.user_prompt_template.value;
            
            // Replace placeholders with actual product data
            prompt = prompt.replace(/\{product_name\}/g, product.name || 'Unknown Product');
            prompt = prompt.replace(/\{product_description\}/g, product.description || 'No description available');
            prompt = prompt.replace(/\{product_price\}/g, product.price || 'Price not available');
            prompt = prompt.replace(/\{product_category\}/g, product.category || 'Uncategorized');
            prompt = prompt.replace(/\{product_sku\}/g, product.url || 'URL not available');
            prompt = prompt.replace(/\{content_type\}/g, this.getContentTypeDisplayName(contentType));
            
            return prompt;
        }
        
        return `Generate ${this.getContentTypeDisplayName(contentType)} content for ${product.name}`;
    },
    
    // Update generation prompt display
    updateGenerationPromptDisplay() {
        const promptDisplay = document.getElementById('llm-generation-prompt');
        
        if (this.selectedProduct) {
            const prompt = this.generatePromptForProduct(this.selectedProduct, this.selectedContentType);
            
            if (this.databasePrompts) {
                const systemPromptElement = document.getElementById('system-prompt-display');
                if (systemPromptElement && this.databasePrompts.system_prompt) {
                    systemPromptElement.textContent = this.databasePrompts.system_prompt.value;
                }
            }
            
            if (promptDisplay) {
                promptDisplay.value = prompt; // Use .value for textarea
            }
        } else {
            if (promptDisplay) {
                promptDisplay.value = 'Select a product to see the generation prompt';
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
