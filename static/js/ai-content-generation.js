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
        
        this.init();
        this.setupLLMControls();
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
                
                // Update generation prompt if we have a data package
                if (this.currentDataPackage && this.currentDataPackage.data_type === 'product') {
                    this.updateLLMConfiguration(this.currentDataPackage);
                }
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
        const generationPrompt = document.getElementById('llm-generation-prompt');
        const llmDataContent = document.getElementById('llm-data-content');
        const llmDataChevron = document.getElementById('llm-data-chevron');
        
        if (llmDataStatus) {
            llmDataStatus.textContent = `Configured for ${dataPackage.data_type}`;
        }
        
        if (generationPrompt && dataPackage.data_type === 'product') {
            const product = dataPackage.source_data;
            const prompt = this.generatePromptForProduct(product, this.selectedContentType);
            generationPrompt.value = prompt;
        }
    }

    // Generate prompt based on product and content type
    generatePromptForProduct(product, contentType) {
        const prompts = {
            feature: `Create a Facebook post highlighting the key features of "${product.name}" (${product.sku}). Price: ${product.price}. Focus on what makes this product unique and appealing. Include relevant hashtags.`,
            benefit: `Create a Facebook post emphasizing the benefits of "${product.name}" (${product.sku}). Price: ${product.price}. Focus on how this product improves the customer's life. Include relevant hashtags.`,
            story: `Create a Facebook post telling a story about "${product.name}" (${product.sku}). Price: ${product.price}. Make it engaging and relatable. Include relevant hashtags.`
        };
        
        return prompts[contentType] || prompts.feature;
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
