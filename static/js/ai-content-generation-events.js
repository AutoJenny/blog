/**
 * AI Content Generation Events Module
 * Event listeners and setup functions
 */

// Add event listener methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
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
        
        // Edit prompt button
        const editPromptBtn = document.getElementById('edit-prompt-btn');
        if (editPromptBtn) {
            editPromptBtn.addEventListener('click', () => this.togglePromptEdit());
        }
    },
    
    setupContentTypeButtons() {
        const contentTypeButtons = document.querySelectorAll('.content-type-btn');
        contentTypeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                contentTypeButtons.forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                // Update selected content type
                this.selectedContentType = e.target.dataset.contentType;
                // Update content text placeholder
                this.updateContentText();
                // Load existing content for new type
                if (this.selectedProduct) {
                    this.loadExistingContent();
                }
            });
        });
    },
    
    setupDataListener() {
        // Listen for data selection events from Item Selection module
        document.addEventListener('dataSelected', (event) => {
            this.handleDataPackage(event.detail);
        });
    },
    
    handleDataPackage(dataPackage) {
        this.currentDataPackage = dataPackage;
        
        if (dataPackage.data_type === 'product') {
            this.setSelectedProduct(dataPackage.data);
            this.updateInputDataDisplay(dataPackage);
            this.updateLLMConfiguration(dataPackage);
        }
    },
    
    updateInputDataDisplay(dataPackage) {
        const inputDataDisplay = document.getElementById('input-data-display');
        const inputDataStatus = document.getElementById('input-data-status');
        
        if (inputDataDisplay && inputDataStatus) {
            inputDataStatus.textContent = `${dataPackage.data_type} selected`;
            
            // Display key product information
            const product = dataPackage.data;
            let displayText = `<strong>${product.name}</strong><br>`;
            
            // Add other relevant fields
            Object.entries(product).forEach(([key, value]) => {
                if (key !== 'name' && value && value !== '') {
                    if (typeof value === 'object') {
                        displayText += `<strong>${key}:</strong> ${JSON.stringify(value)}<br>`;
                    } else {
                        displayText += `<strong>${key}:</strong> ${value}<br>`;
                    }
                }
            });
            
            inputDataDisplay.innerHTML = displayText;
        }
    },
    
    updateLLMConfiguration(dataPackage) {
        const llmDataStatus = document.getElementById('llm-data-status');
        
        if (llmDataStatus) {
            llmDataStatus.textContent = `LLM configured for ${dataPackage.data_type}`;
        }
        
        // Update prompt display
        this.updateGenerationPromptDisplay();
    }
});
