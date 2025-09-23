/**
 * AI Content Generation Data Module
 * Data handling and persistence functions
 */

// Add data-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Load prompts from database
    async loadDatabasePrompts() {
        try {
            const response = await fetch('/launchpad/api/syndication/get-prompts');
            const data = await response.json();
            
            if (data.success) {
                this.databasePrompts = data.prompts;
                console.log('Loaded database prompts:', this.databasePrompts);
            } else {
                console.log('No prompts endpoint available, using defaults');
                this.databasePrompts = null;
            }
        } catch (error) {
            console.log('Prompts endpoint not available, using defaults');
            this.databasePrompts = null;
        }
    },
    
    // Save generated content to database
    async saveGeneratedContent(content, contentType) {
        if (!this.selectedProduct) return;
        
        try {
            const response = await fetch('/launchpad/api/syndication/save-generated-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: this.selectedProduct.id,
                    content_type: contentType,
                    content: content
                })
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('Generated content saved successfully');
            } else {
                console.error('Failed to save generated content:', data.error);
            }
        } catch (error) {
            console.error('Error saving generated content:', error);
        }
    },
    
    // Load existing generated content for the selected product
    async loadExistingContent() {
        if (!this.selectedProduct) {
            console.log('No selected product, skipping content load');
            return;
        }
        
        console.log('Loading existing content for product:', this.selectedProduct.name, 'type:', this.selectedContentType);
        
        try {
            const response = await fetch(`/launchpad/api/syndication/get-generated-content/${this.selectedProduct.id}/${this.selectedContentType}`);
            const data = await response.json();
            
            console.log('Load existing content response:', data);
            
            if (data.success && data.content) {
                this.generatedContent = data.content;
                this.displayGeneratedContent();
                this.enableContentActions();
                this.updateAIStatusHeader(); // Update the accordion header
                console.log('Loaded existing content for', this.selectedProduct.name);
            } else {
                console.log('No existing content found for', this.selectedProduct.name);
            }
        } catch (error) {
            console.error('Error loading existing content:', error);
        }
    },
    
    // Save prompt template to database
    async savePromptTemplate(promptText) {
        try {
            const response = await fetch('/launchpad/api/syndication/save-prompt-template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt_template: promptText
                })
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('Prompt template saved successfully');
                // Update local database prompts
                if (this.databasePrompts) {
                    this.databasePrompts.user_prompt_template.value = promptText;
                }
                // Show success message
                this.showNotification('Prompt template updated successfully', 'success');
            } else {
                console.error('Failed to save prompt:', data.error);
                alert('Failed to save prompt: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving prompt:', error);
            alert('Error saving prompt: ' + error.message);
        }
    }
});
