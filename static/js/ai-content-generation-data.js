/**
 * AI Content Generation Data Module
 * Data handling and persistence functions
 */

// Add data-related methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Load prompts from database
    async loadDatabasePrompts() {
        try {
            const processId = this.processId || 1; // Default to blog posts
            const response = await fetch(`/launchpad/api/syndication/llm-prompts/${processId}`);
            const data = await response.json();
            
            if (data.success) {
                this.databasePrompts = data.prompts;
                console.log('Prompts loaded successfully:', this.databasePrompts);
                // Always update system prompt when loaded
                this.updateSystemPromptDisplay();
                // Update the generation prompt display if data is already selected
                if (this.selectedData) {
                    this.updateGenerationPromptDisplay();
                }
            } else {
                console.log('Failed to load prompts:', data);
                this.databasePrompts = null;
            }
        } catch (error) {
            console.log('Error loading prompts:', error);
            this.databasePrompts = null;
        }
    },
    
           // Save generated content to database
           async saveGeneratedContent(content, contentType) {
               if (!this.selectedData) return;
               
               try {
                   const isProduct = this.processId === 6;
                   const requestBody = {
                       content_type: isProduct ? 'product' : 'blog_post',
                       content: content
                   };
                   
                   if (isProduct) {
                       // For products, use product_id
                       requestBody.product_id = this.selectedData.id;
                   } else {
                       // For blog sections, use section_id and include image data
                       requestBody.section_id = this.selectedData.id;
                       requestBody.section_image_filename = this.selectedData.section_image_filename;
                       requestBody.section_image_url = this.selectedData.section_image_url;
                       requestBody.section_title = this.selectedData.section_title;
                       requestBody.post_title = this.selectedData.post_title;
                   }
                   
                   const response = await fetch('/launchpad/api/syndication/save-generated-content', {
                       method: 'POST',
                       headers: {
                           'Content-Type': 'application/json',
                       },
                       body: JSON.stringify(requestBody)
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
    
    // Load existing generated content for the selected item
    async loadExistingContent() {
        if (!this.selectedData) {
            console.log('No selected data, skipping content load');
            return;
        }
        
        const itemName = this.selectedData.name || this.selectedData.section_title || 'item';
        console.log('Loading existing content for item:', itemName, 'type:', this.selectedContentType);
        
        try {
            const contentType = this.processId === 6 ? 'product' : 'blog_post';
            const itemId = this.selectedData.id;
            const response = await fetch(`/launchpad/api/syndication/get-generated-content/${itemId}/${contentType}`);
            const data = await response.json();
            
            console.log('Load existing content response:', data);
            
            if (data.success && data.content) {
                this.generatedContent = data.content;
                this.displayGeneratedContent();
                this.enableContentActions();
                this.updateAIStatusHeader(); // Update the accordion header
                console.log('Loaded existing content and updated header');
            } else {
                this.generatedContent = ''; // Clear any existing content
                this.updateAIStatusHeader(); // Update header to show "Needs generation"
                console.log('No existing content found');
            }
        } catch (error) {
            console.error('Error loading existing content:', error);
        }
    },
    
           // Save prompt template to database
           async savePromptTemplate(promptText) {
               try {
                   const processId = this.processId || 1; // Default to blog posts
                   const response = await fetch(`/launchpad/api/syndication/llm-prompts/${processId}`, {
                       method: 'PUT',
                       headers: {
                           'Content-Type': 'application/json',
                       },
                       body: JSON.stringify({
                           config_key: 'user_prompt_template',
                           config_value: promptText
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
