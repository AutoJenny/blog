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
            prompt = prompt.replace(/\{content_type\}/g, this.getContentTypeDisplayName(contentType));
            
            return prompt;
        }
        
        return `Generate ${this.getContentTypeDisplayName(contentType)} content for ${product.name}`;
    },
    
    // Update generation prompt display
    updateGenerationPromptDisplay() {
        const promptDisplay = document.getElementById('generation-prompt-display');
        
        if (this.selectedProduct) {
            const prompt = this.generatePromptForProduct(this.selectedProduct, this.selectedContentType);
            
            if (this.databasePrompts) {
                const systemPromptElement = document.getElementById('system-prompt-display');
                if (systemPromptElement && this.databasePrompts.system_prompt) {
                    systemPromptElement.textContent = this.databasePrompts.system_prompt.value;
                }
            }
            
            if (promptDisplay) {
                promptDisplay.textContent = prompt;
            }
        } else {
            if (promptDisplay) {
                promptDisplay.textContent = 'Select a product to see the generation prompt';
            }
        }
    },
    
    // Toggle prompt edit mode
    togglePromptEdit() {
        const promptDisplay = document.getElementById('generation-prompt-display');
        const promptEdit = document.getElementById('generation-prompt-edit');
        const editBtn = document.getElementById('edit-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        
        if (this.isPromptEditMode) {
            // Save mode - save the prompt
            const promptText = promptEdit.value;
            this.savePromptTemplate(promptText);
            
            // Switch back to display mode
            this.isPromptEditMode = false;
            promptDisplay.style.display = 'block';
            promptEdit.style.display = 'none';
            editBtn.textContent = 'Edit Prompt';
            saveBtn.style.display = 'none';
        } else {
            // Edit mode - show edit textarea
            this.isPromptEditMode = true;
            promptDisplay.style.display = 'none';
            promptEdit.style.display = 'block';
            editBtn.textContent = 'Save Prompt';
            saveBtn.style.display = 'inline-block';
            
            // Populate edit textarea with current prompt
            if (this.databasePrompts && this.databasePrompts.user_prompt_template) {
                promptEdit.value = this.databasePrompts.user_prompt_template.value;
            }
            
            promptEdit.focus();
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
