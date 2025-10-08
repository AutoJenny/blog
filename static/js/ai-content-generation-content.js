/**
 * AI Content Generation Content Module
 * Content generation, display, and editing functions
 */

// Add content-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Generate content using AI
    async generateContent() {
        // Check if a product is selected
        if (!window.itemSelectionManager || !window.itemSelectionManager.selectedProduct) {
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
        // Get the selected product ID from the item selection manager
        if (!window.itemSelectionManager || !window.itemSelectionManager.selectedProduct) {
            throw new Error('No product selected. Please select a product first.');
        }
        
        const productId = window.itemSelectionManager.selectedProduct.id;
        const contentType = this.selectedContentType || 'product';
        
        try {
            const response = await fetch('/launchpad/api/syndication/generate-social-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    content_type: contentType
                })
            });
            
            const data = await response.json();
            console.log('LLM API response:', data);
            
            if (data.success && data.content) {
                this.generatedContent = data.content;
            } else {
                console.error('LLM API error:', data);
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
    async addToQueue(silent = false) {
        if (!this.generatedContent) {
            if (!silent) alert('No content to add to queue');
            return false;
        }
        
        if (!this.selectedData) {
            if (!silent) alert('No item selected');
            return false;
        }
        
        try {
            // Prepare request body based on content type
            const isProduct = this.processId === 6;
            const requestBody = {
                content_type: isProduct ? 'product' : 'blog_post',
                status: 'ready'
            };
            
            if (isProduct) {
                requestBody.product_id = this.selectedData.id;
            } else {
                requestBody.section_id = this.selectedData.id;
            }
            
            // Update the queue status from 'draft' to 'ready'
            const response = await fetch('/launchpad/api/syndication/update-queue-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Dispatch event to notify other modules
                const event = new CustomEvent('contentQueued', {
                    detail: {
                        item: this.selectedData,
                        content: this.generatedContent,
                        contentType: this.selectedContentType
                    }
                });
                document.dispatchEvent(event);
                
                if (!silent) {
                    this.showNotification('Content added to posting queue', 'success');
                }
                return true;
            } else {
                if (!silent) {
                    this.showNotification('Failed to add content to queue: ' + data.error, 'error');
                }
                return false;
            }
        } catch (error) {
            console.error('Error adding to queue:', error);
            if (!silent) {
                this.showNotification('Error adding content to queue: ' + error.message, 'error');
            }
            return false;
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
