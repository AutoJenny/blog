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
            // Generate content using real AI
            await this.generateAIContent();
            
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
    
    // Generate content using real AI
    async generateAIContent() {
        const prompt = this.generatePromptForProduct(this.selectedProduct, this.selectedContentType);
        
        try {
            const response = await fetch('/llm-actions/api/llm/actions/16/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: 'ollama',
                    model: 'mistral',
                    input_data: {
                        section_heading: `${this.getContentTypeDisplayName(this.selectedContentType)} Post`,
                        section_description: `Create engaging social media content for ${this.selectedProduct.name}`,
                        ideas_to_include: prompt
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                this.generatedContent = data.result;
            } else {
                throw new Error(data.error || 'Failed to generate content');
            }
        } catch (error) {
            console.error('AI generation error:', error);
            throw error;
        }
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
            editBtn.disabled = false;
        }
        
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.style.display = 'inline-block';
            addToQueueBtn.disabled = false;
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
    async addToQueue() {
        if (!this.generatedContent) {
            alert('No content to add to queue');
            return;
        }
        
        if (!this.selectedProduct) {
            alert('No product selected');
            return;
        }
        
        try {
            // Update the queue status from 'draft' to 'pending'
            const response = await fetch('/launchpad/api/syndication/update-queue-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: this.selectedProduct.id,
                    content_type: this.selectedContentType,
                    status: 'ready'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
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
            } else {
                this.showNotification('Failed to add content to queue: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error adding to queue:', error);
            this.showNotification('Error adding content to queue: ' + error.message, 'error');
        }
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
