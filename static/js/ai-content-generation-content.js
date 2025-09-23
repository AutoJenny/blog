/**
 * AI Content Generation Content Module
 * Content generation, display, and editing functions
 */

// Add content-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Generate content using AI
    async generateContent() {
        if (!this.selectedProduct) {
            alert('Please select a product first');
            return;
        }
        
        const generateBtn = document.getElementById('generate-content-btn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        }
        
        try {
            // Simulate content generation (replace with actual AI call)
            await this.simulateContentGeneration();
            
            // Save generated content
            await this.saveGeneratedContent(this.generatedContent, this.selectedContentType);
            
            // Update UI
            this.displayGeneratedContent();
            this.enableContentActions();
            this.updateAIStatusHeader();
            
        } catch (error) {
            console.error('Error generating content:', error);
            alert('Error generating content: ' + error.message);
        } finally {
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Post';
            }
        }
    },
    
    // Simulate content generation (replace with actual AI call)
    async simulateContentGeneration() {
        return new Promise((resolve) => {
            setTimeout(() => {
                const prompt = this.generatePromptForProduct(this.selectedProduct, this.selectedContentType);
                this.generatedContent = `Generated ${this.selectedContentType} content for ${this.selectedProduct.name}:\n\n${prompt}\n\nThis is simulated content. Replace with actual AI generation.`;
                resolve();
            }, 2000);
        });
    },
    
    // Display generated content in the text area
    displayGeneratedContent() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.textContent = this.generatedContent;
        }
    },
    
    // Enable content action buttons
    enableContentActions() {
        const editBtn = document.getElementById('edit-content-btn');
        if (editBtn) {
            editBtn.style.display = 'inline-block';
        }
        
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.style.display = 'inline-block';
        }
    },
    
    // Edit content in the text area
    editContent() {
        if (!this.generatedContent) {
            alert('No content to edit');
            return;
        }
        
        const contentText = document.getElementById('generated-content-text');
        if (contentText) {
            contentText.focus();
            contentText.select();
        }
    },
    
    // Add content to posting queue
    addToQueue() {
        if (!this.generatedContent) {
            alert('No content to add to queue');
            return;
        }
        
        if (!this.selectedProduct) {
            alert('No product selected');
            return;
        }
        
        // Dispatch event to notify other modules
        const event = new CustomEvent('contentQueued', {
            detail: {
                product: this.selectedProduct,
                content: this.generatedContent,
                contentType: this.selectedContentType
            }
        });
        document.dispatchEvent(event);
        
        this.showNotification('Content added to posting queue', 'success');
    },
    
    // Get content type display name
    getContentTypeDisplayName(contentType) {
        switch (contentType) {
            case 'feature':
                return 'Feature Post';
            case 'benefit':
                return 'Benefit Post';
            case 'story':
                return 'Story Post';
            case 'call_to_action':
                return 'Call to Action';
            default:
                return contentType;
        }
    }
});
