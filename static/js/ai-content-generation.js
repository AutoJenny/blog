/**
 * AI Content Generation Manager
 * Handles AI-powered content generation for syndication pages
 */
class AIContentGenerationManager {
    constructor() {
        this.selectedContentType = 'feature';
        this.generatedContent = '';
        this.selectedProduct = null;
        this.currentDataPackage = null;
        this.databasePrompts = null; // Store prompts from database
        this.isPromptEditMode = false; // Track if prompt is in edit mode
        
        this.init();
        this.setupLLMControls();
        this.loadDatabasePrompts(); // Load prompts from database
    }
    
    init() {
        this.setupEventListeners();
        this.setupContentTypeButtons();
        this.setupDataListener();
    }
    
    setupEventListeners() {
        // Start Ollama button
        const startOllamaBtn = document.getElementById('start-ollama-btn');
        if (startOllamaBtn) {
            startOllamaBtn.addEventListener('click', () => this.startOllama());
        }
        
        // Generate content button
        const generateBtn = document.getElementById('generate-content-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateContent());
        }
        
        // Edit content button
        const editBtn = document.getElementById('edit-content-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.editContent());
        }
        
        // Add to queue button
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.addEventListener('click', () => this.addToQueue());
        }
        
        // Edit generation prompt button
        const editPromptBtn = document.getElementById('edit-generation-prompt-btn');
        if (editPromptBtn) {
            editPromptBtn.addEventListener('click', () => this.togglePromptEdit());
        }
    }
    
    setupContentTypeButtons() {
        const buttons = document.querySelectorAll('.content-type-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                buttons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                button.classList.add('active');
                // Update selected content type
                this.selectedContentType = button.dataset.type;
                
                // Update generation prompt display when content type changes
                this.updateGenerationPromptDisplay();
            });
        });
    }
    
    startOllama() {
        const btn = document.getElementById('start-ollama-btn');
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        // Simulate Ollama startup
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-check"></i> Ollama Ready';
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-success');
            
            // Enable generate button if product is selected
            this.updateGenerateButton();
        }, 2000);
    }
    
    setSelectedProduct(product) {
        this.selectedProduct = product;
        this.updateGenerateButton();
        this.updateContentText();
    }
    
    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-content-btn');
        const ollamaBtn = document.getElementById('start-ollama-btn');
        
        if (generateBtn) {
            const isOllamaReady = ollamaBtn && ollamaBtn.classList.contains('btn-success');
            const hasProduct = this.selectedProduct !== null;
            
            generateBtn.disabled = !(isOllamaReady && hasProduct);
        }
    }
    
    updateContentText() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            if (this.selectedProduct) {
                contentText.innerHTML = `Ready to generate ${this.selectedContentType} content for: <strong>${this.selectedProduct.name}</strong>`;
            } else {
                contentText.innerHTML = 'Select a product and click "Generate Post" to create AI-powered content.';
            }
        }
    }
    
    async generateContent() {
        if (!this.selectedProduct) {
            alert('Please select a product first.');
            return;
        }
        
        const generateBtn = document.getElementById('generate-content-btn');
        const originalText = generateBtn.innerHTML;
        
        try {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            
            // Simulate AI content generation
            await this.simulateContentGeneration();
            
            // Show generated content
            this.displayGeneratedContent();
            
            // Enable edit and add to queue buttons
            this.enableContentActions();
            
        } catch (error) {
            console.error('Error generating content:', error);
            alert('Error generating content. Please try again.');
            this.updateStatusDisplay('Error generating content');
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalText;
        }
    }
    
    async simulateContentGeneration() {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Generate sample content based on content type and product
        const product = this.selectedProduct;
        const contentType = this.selectedContentType;
        
        let content = '';
        
        switch (contentType) {
            case 'feature':
                content = `🔥 Discover ${product.name}! ${product.description || 'Amazing features that will transform your experience.'} Perfect for anyone looking to upgrade their setup. #${product.name.replace(/\s+/g, '')} #Innovation #Tech`;
                break;
            case 'benefit':
                content = `✨ Why ${product.name}? Because it delivers real results! ${product.description || 'Experience the difference with our premium quality and innovative design.'} Don't miss out on this game-changer! #${product.name.replace(/\s+/g, '')} #Benefits #Quality`;
                break;
            case 'story':
                content = `📖 Here's why ${product.name} changed everything for us... ${product.description || 'From the moment we started using it, we knew this was something special.'} Sometimes the best discoveries come from taking a chance. #${product.name.replace(/\s+/g, '')} #Story #Innovation`;
                break;
        }
        
        this.generatedContent = content;
    }
    
    displayGeneratedContent() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.innerHTML = `
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 10px 0;">
                    <div style="color: #10b981; font-weight: 600; margin-bottom: 8px;">
                        <i class="fas fa-robot"></i> Generated ${this.selectedContentType.charAt(0).toUpperCase() + this.selectedContentType.slice(1)} Content:
                    </div>
                    <div style="color: #f1f5f9; line-height: 1.5;">
                        ${this.generatedContent}
                    </div>
                </div>
            `;
        }
    }
    
    enableContentActions() {
        const editBtn = document.getElementById('edit-content-btn');
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        
        if (editBtn) {
            editBtn.disabled = false;
            editBtn.style.display = 'inline-block';
        }
        
        if (addToQueueBtn) {
            addToQueueBtn.disabled = false;
            addToQueueBtn.style.display = 'inline-block';
        }
    }
    
    editContent() {
        if (!this.generatedContent) {
            alert('No content to edit. Please generate content first.');
            return;
        }
        
        const newContent = prompt('Edit the generated content:', this.generatedContent);
        if (newContent !== null && newContent.trim() !== '') {
            this.generatedContent = newContent.trim();
            this.displayGeneratedContent();
        }
    }
    
    addToQueue() {
        if (!this.generatedContent) {
            alert('No content to add to queue. Please generate content first.');
            return;
        }
        
        if (!this.selectedProduct) {
            alert('No product selected. Please select a product first.');
            return;
        }
        
        // Add to queue logic would go here
        // For now, just show a success message
        alert(`Content added to queue for ${this.selectedProduct.name}!`);
        
        // Reset the form
        this.resetForm();
    }
    
    resetForm() {
        this.generatedContent = '';
        this.selectedProduct = null;
        
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.innerHTML = 'Select a product and click "Generate Post" to create AI-powered content.';
        }
        
        const editBtn = document.getElementById('edit-content-btn');
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        
        if (editBtn) {
            editBtn.disabled = true;
            editBtn.style.display = 'none';
        }
        
        if (addToQueueBtn) {
            addToQueueBtn.disabled = true;
            addToQueueBtn.style.display = 'none';
        }
        
        this.updateGenerateButton();
    }

    // Setup listener for dataSelected events
    setupDataListener() {
        document.addEventListener('dataSelected', (event) => {
            this.handleDataPackage(event.detail.dataPackage);
        });
    }

    // Handle incoming data package
    handleDataPackage(dataPackage) {
        this.currentDataPackage = dataPackage;
        
        // Update input data display
        this.updateInputDataDisplay(dataPackage);
        
        // Update LLM configuration based on data type
        this.updateLLMConfiguration(dataPackage);
        
        // Extract product data for backward compatibility
        if (dataPackage.data_type === 'product') {
            this.selectedProduct = dataPackage.source_data;
            this.updateGenerateButton();
            this.updateContentText();
        }
    }

    // Update input data accordion display
    updateInputDataDisplay(dataPackage) {
        const inputDataDisplay = document.getElementById('input-data-display');
        const inputDataStatus = document.getElementById('input-data-status');
        const inputDataContent = document.getElementById('input-data-content');
        const inputDataChevron = document.getElementById('input-data-chevron');
        
        if (inputDataDisplay && inputDataStatus) {
            const displayData = {
                'Data Type': dataPackage.data_type,
                'Platform': `${dataPackage.platform.display_name} (${dataPackage.platform.name})`,
                'Channel': `${dataPackage.channel_type.display_name} (${dataPackage.channel_type.name})`,
                'Source Data': dataPackage.source_data,
                'Generation Config': dataPackage.generation_config,
                'Timestamp': new Date(dataPackage.timestamp).toLocaleString()
            };
            
            let html = '';
            for (const [key, value] of Object.entries(displayData)) {
                html += `<div style="margin-bottom: 8px;"><strong style="color: #f59e0b;">${key}:</strong> `;
                if (typeof value === 'object') {
                    html += `<pre style="display: inline; color: #e2e8f0;">${JSON.stringify(value, null, 2)}</pre>`;
                } else {
                    html += `<span style="color: #e2e8f0;">${value}</span>`;
                }
                html += `</div>`;
            }
            
            inputDataDisplay.innerHTML = html;
            inputDataStatus.textContent = `${dataPackage.data_type} from ${dataPackage.platform.display_name}`;
        }
    }

    // Update LLM configuration based on data package
    updateLLMConfiguration(dataPackage) {
        const llmDataStatus = document.getElementById('llm-data-status');
        const llmDataContent = document.getElementById('llm-data-content');
        const llmDataChevron = document.getElementById('llm-data-chevron');
        
        if (llmDataStatus) {
            const promptSource = this.databasePrompts ? 'Database prompts' : 'Default prompts';
            llmDataStatus.textContent = `${promptSource} - ${dataPackage.data_type}`;
        }
        
        // Update generation prompt display
        this.updateGenerationPromptDisplay();
    }

    // Load LLM prompts from database
    async loadDatabasePrompts() {
        try {
            // Get process_id from page data (Facebook Product Post = 1)
            const processId = 1; // TODO: Make this dynamic based on platform/channel
            
            const response = await fetch(`/launchpad/api/syndication/llm-prompts/${processId}`);
            const data = await response.json();
            
            if (data.success) {
                this.databasePrompts = data.prompts;
                console.log('Loaded database prompts:', this.databasePrompts);
                
                // Update system prompt in UI if available
                const systemPromptElement = document.getElementById('llm-system-prompt');
                if (systemPromptElement && this.databasePrompts.system_prompt) {
                    systemPromptElement.value = this.databasePrompts.system_prompt.value;
                }
                
                // Update generation prompt display after prompts are loaded
                this.updateGenerationPromptDisplay();
            } else {
                console.warn('Failed to load database prompts:', data.error);
                // Update generation prompt display even if database prompts failed
                this.updateGenerationPromptDisplay();
            }
        } catch (error) {
            console.error('Error loading database prompts:', error);
            // Update generation prompt display even if there was an error
            this.updateGenerationPromptDisplay();
        }
    }

    // Generate prompt based on product and content type using database template
    generatePromptForProduct(product, contentType) {
        // Use database template if available
        if (this.databasePrompts && this.databasePrompts.user_prompt_template) {
            const template = this.databasePrompts.user_prompt_template.value;
            
            // Map content types to descriptive text
            const contentTypeDescriptions = {
                'feature': 'Feature Focus: Highlight key features and what makes this product unique',
                'benefit': 'Benefit Focus: Emphasize how this product improves the customer\'s life',
                'story': 'Story Focus: Tell an engaging, relatable story about the product'
            };
            
            // Replace placeholders in template
            let prompt = template
                .replace(/{product_name}/g, product.name || 'Unknown Product')
                .replace(/{product_sku}/g, product.sku || 'N/A')
                .replace(/{product_price}/g, product.price || 'N/A')
                .replace(/{product_description}/g, product.description || 'No description available')
                .replace(/{content_type}/g, contentTypeDescriptions[contentType] || contentTypeDescriptions['feature']);
            
            return prompt;
        }
        
        // Fallback to hard-coded prompts if database template not available
        const fallbackPrompts = {
            feature: `Create a Facebook post highlighting the key features of "${product.name}" (${product.sku}). Price: ${product.price}. Focus on what makes this product unique and appealing. Include relevant hashtags.`,
            benefit: `Create a Facebook post emphasizing the benefits of "${product.name}" (${product.sku}). Price: ${product.price}. Focus on how this product improves the customer's life. Include relevant hashtags.`,
            story: `Create a Facebook post telling a story about "${product.name}" (${product.sku}). Price: ${product.price}. Make it engaging and relatable. Include relevant hashtags.`
        };
        
        return fallbackPrompts[contentType] || fallbackPrompts.feature;
    }

    // Update generation prompt display based on current state
    updateGenerationPromptDisplay() {
        const generationPrompt = document.getElementById('llm-generation-prompt');
        if (!generationPrompt) return;

        // Don't update if in edit mode
        if (this.isPromptEditMode) return;

        // If we have a selected product, show the actual prompt
        if (this.selectedProduct) {
            const prompt = this.generatePromptForProduct(this.selectedProduct, this.selectedContentType);
            generationPrompt.value = prompt;
        } else {
            // No product selected - show informative message
            if (this.databasePrompts) {
                generationPrompt.value = 'Select a product from Item Selection to see the generation prompt with your specific product data.';
            } else {
                generationPrompt.value = 'Select a product from Item Selection to see the generation prompt. Database prompts not available - using fallback prompts.';
            }
        }
    }

    // Toggle prompt edit mode
    togglePromptEdit() {
        const generationPrompt = document.getElementById('llm-generation-prompt');
        const editBtn = document.getElementById('edit-generation-prompt-btn');
        
        if (!generationPrompt || !editBtn) return;

        this.isPromptEditMode = !this.isPromptEditMode;

        if (this.isPromptEditMode) {
            // Enter edit mode
            generationPrompt.readOnly = false;
            generationPrompt.style.border = '1px solid #f59e0b';
            editBtn.innerHTML = '<i class="fas fa-save"></i> Save';
            editBtn.classList.remove('btn-secondary');
            editBtn.classList.add('btn-primary');
        } else {
            // Exit edit mode and save
            generationPrompt.readOnly = true;
            generationPrompt.style.border = '1px solid #334155';
            editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
            editBtn.classList.remove('btn-primary');
            editBtn.classList.add('btn-secondary');
            
            // Save the edited prompt to database
            this.saveEditedPrompt(generationPrompt.value);
        }
    }

    // Save edited prompt to database
    async saveEditedPrompt(promptText) {
        try {
            const processId = 1; // TODO: Make this dynamic based on platform/channel
            
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
                console.log('Prompt saved successfully');
                // Update local database prompts
                if (this.databasePrompts) {
                    this.databasePrompts.user_prompt_template.value = promptText;
                }
            } else {
                console.error('Failed to save prompt:', data.error);
                alert('Failed to save prompt: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving prompt:', error);
            alert('Error saving prompt: ' + error.message);
        }
    }

    // Setup LLM controls
    setupLLMControls() {
        const temperatureSlider = document.getElementById('llm-temperature');
        const temperatureValue = document.getElementById('temperature-value');
        
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
        }
    }
}

// Initialize AI Content Generation Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiContentGenerationManager = new AIContentGenerationManager();
});
